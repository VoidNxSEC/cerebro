#!/usr/bin/env python3
"""
AUDITORIA DEFINITIVA DE CRÉDITOS via BigQuery
Baseado no Relatório Técnico - Seção 5.2

Este script valida SE e COMO os créditos promocionais estão sendo aplicados.
Resolve o problema da latência do painel de billing padrão.
"""
import os
import sys
from google.cloud import bigquery
from google.auth import default
from datetime import datetime, timedelta

def get_billing_export_table():
    """
    Detecta automaticamente a tabela de export do Cloud Billing.

    IMPORTANTE: Você precisa ter configurado o Billing Export primeiro!
    Console: https://console.cloud.google.com/billing/export
    """
    _, project = default()

    # Padrão de nomenclatura do GCP
    # Format: gcp_billing_export_v1_XXXXXX-XXXXXX-XXXXXX
    dataset_id = os.getenv("BILLING_EXPORT_DATASET", "billing_export")
    table_pattern = os.getenv("BILLING_EXPORT_TABLE")

    if not table_pattern:
        print("⚠️  BILLING_EXPORT_TABLE não configurado")
        print("\n🔧 SETUP NECESSÁRIO:")
        print("1. Vá para: https://console.cloud.google.com/billing/export")
        print("2. Configure 'Detailed usage cost' para BigQuery")
        print("3. Anote o nome da tabela (formato: gcp_billing_export_v1_XXXXXX_XXXXXX_XXXXXX)")
        print("4. Export:")
        print(f"   export BILLING_EXPORT_DATASET='seu_dataset'")
        print(f"   export BILLING_EXPORT_TABLE='gcp_billing_export_v1_...'")
        return None

    return f"{project}.{dataset_id}.{table_pattern}"

def audit_credit_consumption(days_back=7):
    """
    Query de auditoria DEFINITIVA - Seção 5.2 do Relatório

    Retorna:
    - Quais serviços foram usados
    - Quanto custou bruto (gross_cost)
    - Quanto foi coberto por crédito (credit_amount)
    - Quanto saiu do bolso (net_cost)
    """
    print("="*60)
    print("🔍 AUDITORIA DE CRÉDITOS - BIGQUERY")
    print("="*60)

    table_ref = get_billing_export_table()
    if not table_ref:
        sys.exit(1)

    print(f"\n📊 Tabela: {table_ref}")
    print(f"📅 Período: Últimos {days_back} dias")

    client = bigquery.Client()

    # Query baseada no Relatório (Seção 5.2) - Adaptada
    query = f"""
    SELECT
      invoice.month,

      -- Detalhes do Serviço Consumido
      service.description AS service_name,
      sku.description AS sku_name,
      sku.id AS sku_id,

      -- Detalhes do Crédito Aplicado
      credits.name AS credit_name,
      credits.type AS credit_type,
      credits.amount AS credit_amount, -- Valor negativo = desconto

      -- Análise Financeira (CRÍTICO!)
      cost AS gross_cost, -- Custo bruto ANTES do crédito
      (cost + IFNULL(credits.amount, 0)) AS net_cost_to_wallet, -- O que SAI DO BOLSO

      -- Uso
      usage.amount AS usage_amount,
      usage.unit AS usage_unit,

      usage_start_time,
      usage_end_time

    FROM
      `{table_ref}`,
      UNNEST(credits) AS credits
    WHERE
      -- Filtragem pelos Créditos Específicos (IDs do CSV fornecido)
      (
        credits.name LIKE '%GenAI App Builder%' OR
        credits.name LIKE '%Dialogflow CX Trial%' OR
        credits.id LIKE '%01fcba1620b82830ec89167e55e859767b7a8525813b0b87545996daede01b04%' OR
        credits.id LIKE '%0195bdacde99b9b9ca3d87c9bf6cfec6ab3d34af5d42edbc30e5e3c856e6b2bd%'
      )

      -- Período de análise
      AND usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days_back} DAY)

    ORDER BY
      usage_start_time DESC
    LIMIT 500
    """

    try:
        print("\n⏳ Executando query no BigQuery...")
        query_job = client.query(query)
        results = query_job.result()

        # Análise dos resultados
        print("\n" + "="*60)
        print("📋 RESULTADOS DA AUDITORIA")
        print("="*60)

        total_gross = 0.0
        total_credits = 0.0
        total_net = 0.0
        rows_found = 0

        for row in results:
            rows_found += 1

            # Acumula totais
            gross = float(row.gross_cost) if row.gross_cost else 0.0
            credit = float(row.credit_amount) if row.credit_amount else 0.0
            net = float(row.net_cost_to_wallet) if row.net_cost_to_wallet else 0.0

            total_gross += gross
            total_credits += credit
            total_net += net

            # Display detalhado (primeiros 10)
            if rows_found <= 10:
                print(f"\n🔹 {row.usage_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   Serviço: {row.service_name}")
                print(f"   SKU: {row.sku_name}")
                print(f"   Crédito: {row.credit_name}")
                print(f"   💰 Custo Bruto: ${gross:.6f}")
                print(f"   💳 Crédito Aplicado: ${credit:.6f}")
                print(f"   💵 Custo Líquido (seu bolso): ${net:.6f}")
                if row.usage_amount:
                    print(f"   📊 Uso: {row.usage_amount} {row.usage_unit}")

        # Sumário Financeiro
        print("\n" + "="*60)
        print("💰 SUMÁRIO FINANCEIRO")
        print("="*60)
        print(f"Total de Transações: {rows_found}")
        print(f"Custo Bruto Total: ${total_gross:.4f}")
        print(f"Créditos Aplicados: ${total_credits:.4f}")
        print(f"Custo Líquido (Pago): ${total_net:.4f}")

        # VALIDAÇÃO CRÍTICA
        print("\n" + "="*60)
        print("✅ VALIDAÇÃO DE CONSUMO DE CRÉDITOS")
        print("="*60)

        if rows_found == 0:
            print("⚠️  NENHUMA TRANSAÇÃO COM CRÉDITO ENCONTRADA")
            print("\nPossíveis causas:")
            print("1. Latência do Billing (aguarde 24-48h)")
            print("2. Você ainda não consumiu nenhum serviço elegível")
            print("3. Os créditos não estão sendo aplicados (problema de configuração)")
        elif abs(total_net) < 0.01:  # Praticamente zero
            print("🎉 SUCESSO TOTAL!")
            print(f"   • Você consumiu ${abs(total_gross):.4f} de serviços")
            print(f"   • Créditos cobriram 100% (${abs(total_credits):.4f})")
            print("   • Você NÃO foi cobrado ($0.00 no cartão)")
        else:
            print("⚠️  ATENÇÃO: Cobrança Parcial Detectada")
            print(f"   • Custo bruto: ${total_gross:.4f}")
            print(f"   • Créditos: ${total_credits:.4f}")
            print(f"   • VOCÊ PAGOU: ${total_net:.4f}")
            print("\n🔧 Action Required:")
            print("   → Revise os SKUs consumidos")
            print("   → Verifique se os serviços são elegíveis")

        return results

    except Exception as e:
        print(f"\n❌ ERRO na query BigQuery: {e}")
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Billing Export configurado?")
        print("2. Permissões de BigQuery (roles/bigquery.user)?")
        print("3. Nome da tabela correto?")
        return None

def check_billing_export_setup():
    """Valida se o Billing Export está configurado"""
    print("🔍 Verificando configuração do Billing Export...")

    _, project = default()
    client = bigquery.Client()

    dataset_id = os.getenv("BILLING_EXPORT_DATASET", "billing_export")

    try:
        dataset = client.get_dataset(dataset_id)
        print(f"✅ Dataset '{dataset_id}' encontrado")

        # Lista tabelas
        tables = list(client.list_tables(dataset))
        if tables:
            print(f"✅ Tabelas de billing encontradas:")
            for table in tables:
                print(f"   - {table.table_id}")
                if table.table_id.startswith("gcp_billing_export"):
                    print(f"\n💡 Use esta tabela:")
                    print(f"   export BILLING_EXPORT_TABLE='{table.table_id}'")
        else:
            print("⚠️  Dataset existe mas está vazio")
            print("   Aguarde alguns minutos após configurar o export")

        return True

    except Exception as e:
        print(f"❌ Dataset '{dataset_id}' não encontrado: {e}")
        print("\n🔧 CONFIGURE O BILLING EXPORT:")
        print("1. https://console.cloud.google.com/billing/export")
        print("2. 'Export detailed usage cost to BigQuery'")
        print(f"3. Crie dataset: {dataset_id}")
        return False

def main():
    print("="*60)
    print("💳 SISTEMA DE AUDITORIA DE CRÉDITOS GCP")
    print("="*60)
    print("\nBaseado no Relatório Técnico - Seção 5.2")
    print("Resolve: Latência do painel + Validação definitiva")

    # Step 1: Verifica setup
    if not check_billing_export_setup():
        print("\n⚠️  Configure o Billing Export primeiro")
        sys.exit(1)

    print("\n" + "="*60)

    # Step 2: Executa auditoria
    days = int(os.getenv("AUDIT_DAYS", "7"))
    results = audit_credit_consumption(days_back=days)

    if results:
        print("\n✅ Auditoria concluída!")
        print("\n📝 PRÓXIMOS PASSOS:")
        print("1. Se net_cost > 0: Revise a arquitetura (você está sendo cobrado)")
        print("2. Se net_cost = 0: Continue consumindo com segurança")
        print("3. Execute diariamente para monitorar")
    else:
        print("\n⚠️  Auditoria não retornou dados")

if __name__ == "__main__":
    main()
