# Phase 3: TUI Screens - IN PROGRESS 🚧

**Data**: 2026-02-02  
**Status**: 🚧 **EM ANDAMENTO** - Estrutura base completa

## Progresso Atual

### ✅ Completado

1. **Estrutura de diretórios TUI**
   ```
   src/phantom/tui/
   ├── __init__.py          ✅ Lazy loading
   ├── app.py              ✅ App principal com navegação
   ├── screens/            ✅ Estrutura criada
   ├── widgets/            ✅ Estrutura criada
   └── commands/           ✅ Estrutura criada
   ```

2. **Aplicação TUI Base** (`app.py`)
   - ✅ Layout com sidebar + conteúdo principal
   - ✅ 6 telas navegáveis (Dashboard, Projects, Intelligence, Scripts, GCP, Logs)
   - ✅ Keyboard shortcuts (q, d, p, i, s, g, l)
   - ✅ Sidebar com botões de navegação
   - ✅ Header com relógio
   - ✅ Footer com bindings
   - ✅ CSS styling básico

3. **Integração CLI**
   - ✅ Comando `cerebro tui` adicionado
   - ✅ Help text com keyboard shortcuts
   - ✅ Lazy loading para evitar importar textual desnecessariamente

4. **Ambiente de Desenvolvimento**
   - ✅ Textual 0.47.1 instalado via Poetry
   - ✅ TUI funciona com `nix develop --command poetry run cerebro tui`

### 🚧 Em Andamento (7 Tasks)

**Task #6**: Implementar DashboardScreen com métricas reais  
**Task #7**: Implementar ProjectsScreen com DataTable  
**Task #8**: Implementar IntelligenceScreen com query interface  
**Task #9**: Implementar ScriptsScreen e GCPCreditsScreen  
**Task #10**: Implementar LogsScreen e widgets customizados  
**Task #11**: Implementar Command Router e integração CLI  
**Task #12**: Documentar Phase 3 e validar funcionalidade  

## Arquitetura Atual

### Aplicação Principal (app.py)

```python
CerebroApp (Textual.App)
├── Sidebar (Vertical)
│   ├── Title: "🧠 CEREBRO"
│   ├── Buttons: Dashboard, Projects, Intelligence, Scripts, GCP, Logs
│   └── Quit button
├── Header (com relógio)
├── Footer (com keybindings)
└── Screens (6)
    ├── DashboardScreen     [placeholder]
    ├── ProjectsScreen      [placeholder]
    ├── IntelligenceScreen  [placeholder]
    ├── ScriptsScreen       [placeholder]
    ├── GCPCreditsScreen    [placeholder]
    └── LogsScreen          [placeholder]
```

### Keyboard Shortcuts Implementados

- `q` - Quit (sair do aplicativo)
- `d` - Dashboard
- `p` - Projects
- `i` - Intelligence
- `s` - Scripts
- `g` - GCP Credits
- `l` - Logs
- `Esc` - Back (voltar para tela anterior)

### CSS Styling

- Sidebar: 20 colunas, border direita primary
- Main content: flex width, padding 2, scrollable
- Buttons: 100% width, margin bottom 1
- Screen titles: bold, border bottom

## Próximos Passos

### Prioridade 1: Dashboard Screen (Task #6)

Implementar métricas em tempo real:

```python
class DashboardScreen(Screen):
    """Dashboard com métricas do sistema."""
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            SystemMetricsPanel(),      # CPU, Mem, Disk
            AlertsPanel(),             # Warnings, errors
            RecentActivityLog(),       # Últimas ações
            QuickActionsButtons(),     # Scan, Index, Query
            id="dashboard-content"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        self.set_interval(5, self.refresh_metrics)
```

**Widgets necessários**:
- `SystemMetricsPanel` - Rich table com métricas sistema
- `AlertsPanel` - Lista de alertas com níveis
- `RecentActivityLog` - Log de últimas ações
- `QuickActionsButtons` - Botões para ações rápidas

### Prioridade 2: Command Router (Task #11)

Criar router para executar comandos CLI e stream results:

```python
class CommandRouter:
    """Roteia ações TUI para funções CLI."""
    
    async def run_command(self, command: str, *args, **kwargs):
        """Execute CLI command and stream output."""
        # Import appropriate CLI function
        # Execute with subprocess or direct call
        # Yield progress updates
        # Return final result
        
    async def run_batch_burn(self, queries: int, workers: int):
        from phantom.commands.gcp import batch_burn
        async for progress in batch_burn(queries, workers):
            yield progress
```

### Prioridade 3: Projects Screen (Task #7)

DataTable com projetos analisados:

```python
class ProjectsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="projects-table")
        yield Footer()
    
    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Name", "Health", "LOC", "Last Scan")
        self.load_projects()
```

## Validação Phase 3

Checklist completo (do plano original):

- ✅ Todas telas navegáveis via sidebar
- ✅ Keyboard shortcuts funcionam
- ⏳ Progress bars atualizam durante operações longas
- ⏳ Pode executar queries via TUI
- ⏳ Pode rodar scripts via TUI
- ⏳ Métricas sistema atualizadas em tempo real

## Testes

### Teste Manual Básico

```bash
# Lançar TUI
nix develop --command poetry run cerebro tui

# Testar navegação
# Pressionar: d, p, i, s, g, l (deve mudar de tela)
# Pressionar: q (deve sair)
```

### Teste de Integração (pendente)

```bash
# Testar comando via TUI
# Dashboard → Quick Action → Scan → Selecionar repo → Executar
# Verificar progress bar atualiza
# Verificar resultado aparece na tela
```

## Métricas de Progresso

**Estrutura**: 100% ✅  
**Navegação básica**: 100% ✅  
**Telas funcionais**: 0% (6 telas pendentes)  
**Command integration**: 0%  
**Widgets customizados**: 0%  

**Total Phase 3**: ~20% completo

## Dependências

- ✅ `textual ^0.47.0` - Framework TUI
- ✅ `textual-dev ^1.5.0` - Dev tools
- ✅ Poetry environment ativo
- ✅ CLI Phase 2 completo (comandos disponíveis)

## Notas Técnicas

### Lazy Loading

O `__init__.py` usa lazy loading para evitar importar textual no import time:

```python
def get_app():
    """Lazy import to avoid loading textual at module import time."""
    from .app import CerebroApp
    return CerebroApp
```

Isso permite que o CLI funcione mesmo se textual não estiver instalado (apenas o comando `tui` falhará).

### Ambiente Poetry

A TUI requer usar `poetry run` porque textual está instalado no virtualenv do Poetry:

```bash
# ❌ NÃO funciona
nix develop --command python -m phantom.tui.app

# ✅ Funciona
nix develop --command poetry run cerebro tui
```

### Textual DevTools

Para debugging, use textual devtools:

```bash
# Terminal 1: Console
nix develop --command poetry run textual console

# Terminal 2: App
nix develop --command poetry run textual run --dev src/phantom/tui/app.py:CerebroApp
```

## Próxima Sessão

**Objetivo**: Implementar DashboardScreen completo (Task #6)

**Passos**:
1. Criar widget `SystemMetricsPanel` em `tui/widgets/status_panel.py`
2. Usar `psutil` para obter métricas reais
3. Adicionar auto-refresh a cada 5s
4. Testar métricas atualizam corretamente

---

**Status**: 🚧 Phase 3 iniciada - estrutura base completa, aguardando implementação de funcionalidades  
**Próximo**: Task #6 - DashboardScreen com métricas reais
