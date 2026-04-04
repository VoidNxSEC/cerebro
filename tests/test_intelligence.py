"""Tests for the Intelligence Core module (cerebro.intelligence.core)."""


import pytest

from cerebro.intelligence.core import (
    CerebroIntelligence,
    EcosystemStatus,
    IntelligenceItem,
    IntelligenceType,
    Project,
    ProjectStatus,
    ThreatLevel,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class TestEnums:
    def test_intelligence_type_values(self):
        assert IntelligenceType.SIGINT.value == "sigint"
        assert IntelligenceType.HUMINT.value == "humint"
        assert IntelligenceType.OSINT.value == "osint"
        assert IntelligenceType.TECHINT.value == "techint"

    def test_threat_level_values(self):
        assert ThreatLevel.CRITICAL.value == "critical"
        assert ThreatLevel.HIGH.value == "high"
        assert ThreatLevel.INFO.value == "info"

    def test_project_status_values(self):
        assert ProjectStatus.ACTIVE.value == "active"
        assert ProjectStatus.ARCHIVED.value == "archived"
        assert ProjectStatus.UNKNOWN.value == "unknown"


# ---------------------------------------------------------------------------
# IntelligenceItem
# ---------------------------------------------------------------------------
class TestIntelligenceItem:
    def test_creation(self):
        item = IntelligenceItem(
            id="test-001",
            type=IntelligenceType.SIGINT,
            source="test-scanner",
            title="Test Signal",
            content="Detected anomaly in project alpha",
        )
        assert item.id == "test-001"
        assert item.type == IntelligenceType.SIGINT
        assert item.threat_level == ThreatLevel.INFO  # default

    def test_to_dict(self):
        item = IntelligenceItem(
            id="test-002",
            type=IntelligenceType.OSINT,
            source="github",
            title="Open Source Finding",
            content="CVE found in dependency",
            threat_level=ThreatLevel.HIGH,
            tags=["security", "cve"],
            related_projects=["alpha"],
        )
        d = item.to_dict()
        assert d["id"] == "test-002"
        assert d["type"] == "osint"
        assert d["threat_level"] == "high"
        assert "security" in d["tags"]
        assert isinstance(d["timestamp"], str)

    def test_from_dict_roundtrip(self):
        item = IntelligenceItem(
            id="test-003",
            type=IntelligenceType.TECHINT,
            source="scanner",
            title="Tech Finding",
            content="Architecture issue detected",
        )
        d = item.to_dict()
        restored = IntelligenceItem.from_dict(d)
        assert restored.id == item.id
        assert restored.type == item.type
        assert restored.title == item.title


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------
class TestProject:
    def test_creation(self, tmp_path):
        p = Project(name="test-project", path=tmp_path)
        assert p.name == "test-project"
        assert p.status == ProjectStatus.UNKNOWN
        assert p.health_score == 0.0

    def test_to_dict(self, tmp_path):
        p = Project(
            name="alpha",
            path=tmp_path,
            languages=["Python", "Nix"],
            status=ProjectStatus.ACTIVE,
            health_score=85.0,
        )
        d = p.to_dict()
        assert d["name"] == "alpha"
        assert d["status"] == "active"
        assert d["health_score"] == 85.0
        assert "Python" in d["languages"]


# ---------------------------------------------------------------------------
# EcosystemStatus
# ---------------------------------------------------------------------------
class TestEcosystemStatus:
    def test_defaults(self):
        es = EcosystemStatus()
        assert es.total_projects == 0
        assert es.health_score == 0.0

    def test_to_dict(self):
        es = EcosystemStatus(total_projects=5, active_projects=3, health_score=75.0)
        d = es.to_dict()
        assert d["total_projects"] == 5
        assert d["active_projects"] == 3


# ---------------------------------------------------------------------------
# CerebroIntelligence
# ---------------------------------------------------------------------------
class TestCerebroIntelligence:
    @pytest.fixture
    def cerebro(self, tmp_path):
        return CerebroIntelligence(
            arch_path=str(tmp_path / "arch"),
            data_dir=str(tmp_path / "data"),
        )

    def test_initialization(self, cerebro):
        assert cerebro.get_project_count() == 0

    def test_register_project(self, cerebro, tmp_path):
        p = Project(name="proj-a", path=tmp_path)
        cerebro.register_project(p)
        assert cerebro.get_project_count() == 1
        assert cerebro.get_project("proj-a") is not None

    def test_list_projects(self, cerebro, tmp_path):
        cerebro.register_project(Project(name="a", path=tmp_path))
        cerebro.register_project(Project(name="b", path=tmp_path))
        assert len(cerebro.list_projects()) == 2

    def test_add_intelligence(self, cerebro):
        item = IntelligenceItem(
            id="int-001",
            type=IntelligenceType.SIGINT,
            source="test",
            title="Test",
            content="Test content",
        )
        cerebro.add_intelligence(item)
        assert cerebro.get_intelligence("int-001") is not None

    def test_add_intelligence_auto_id(self, cerebro):
        item = IntelligenceItem(
            id="",
            type=IntelligenceType.OSINT,
            source="test",
            title="Auto ID",
            content="Should get an auto-generated ID",
        )
        new_id = cerebro.add_intelligence(item)
        assert new_id != ""
        assert cerebro.get_intelligence(new_id) is not None

    def test_query_intelligence(self, cerebro):
        cerebro.add_intelligence(IntelligenceItem(
            id="q-001",
            type=IntelligenceType.TECHINT,
            source="scanner",
            title="Architecture Issue",
            content="Circular dependency found in module alpha",
        ))
        results = cerebro.query_intelligence("circular dependency")
        assert len(results) == 1
        assert results[0].id == "q-001"

    def test_query_intelligence_type_filter(self, cerebro):
        cerebro.add_intelligence(IntelligenceItem(
            id="f-001", type=IntelligenceType.SIGINT,
            source="test", title="Signal", content="signal data",
        ))
        cerebro.add_intelligence(IntelligenceItem(
            id="f-002", type=IntelligenceType.OSINT,
            source="test", title="Open Source", content="signal data",
        ))
        results = cerebro.query_intelligence("signal", types=[IntelligenceType.SIGINT])
        assert len(results) == 1
        assert results[0].type == IntelligenceType.SIGINT

    def test_calculate_health_score_empty(self, cerebro):
        assert cerebro.calculate_health_score() == 0.0

    def test_calculate_health_score(self, cerebro, tmp_path):
        cerebro.register_project(Project(name="a", path=tmp_path, health_score=80.0))
        cerebro.register_project(Project(name="b", path=tmp_path, health_score=60.0))
        assert cerebro.calculate_health_score() == 70.0

    def test_get_alerts_low_health(self, cerebro, tmp_path):
        cerebro.register_project(Project(name="sick", path=tmp_path, health_score=30.0))
        alerts = cerebro.get_alerts()
        assert any(a["type"] == "low_health" for a in alerts)

    def test_generate_briefing(self, cerebro, tmp_path):
        cerebro.register_project(Project(name="a", path=tmp_path, status=ProjectStatus.ACTIVE, health_score=90.0))
        briefing = cerebro.generate_briefing()
        assert briefing["classification"] == "INTERNAL"
        assert briefing["ecosystem"]["total_projects"] == 1

    def test_save_and_reload(self, tmp_path):
        c1 = CerebroIntelligence(arch_path=str(tmp_path / "arch"), data_dir=str(tmp_path / "data"))
        c1.register_project(Project(name="persistent", path=tmp_path, status=ProjectStatus.ACTIVE))
        c1.save()

        c2 = CerebroIntelligence(arch_path=str(tmp_path / "arch"), data_dir=str(tmp_path / "data"))
        assert c2.get_project("persistent") is not None

    def test_generate_id(self, cerebro):
        id1 = cerebro.generate_id("content-a")
        id2 = cerebro.generate_id("content-b")
        assert id1 != id2
        assert len(id1) == 16
