import pytest
from pydantic import ValidationError

from src.mcp.schemas import (
    GetByDomainInput,
    GetNewsInput,
    GetProfileInput,
    SearchInput,
)


class TestGetNewsInput:
    def test_valid_defaults(self):
        inp = GetNewsInput(profil="ETUDIANT")
        assert inp.profil == "ETUDIANT"
        assert inp.periode == "24h"
        assert inp.nb_articles == 10
        assert inp.domaines == []

    def test_invalid_profil(self):
        with pytest.raises(ValidationError):
            GetNewsInput(profil="ADMIN")

    def test_nb_articles_minimum(self):
        with pytest.raises(ValidationError):
            GetNewsInput(profil="ETUDIANT", nb_articles=0)

    def test_nb_articles_maximum(self):
        with pytest.raises(ValidationError):
            GetNewsInput(profil="ETUDIANT", nb_articles=51)

    def test_nb_articles_boundary_valid(self):
        assert GetNewsInput(profil="ETUDIANT", nb_articles=1).nb_articles == 1
        assert GetNewsInput(profil="ETUDIANT", nb_articles=50).nb_articles == 50

    def test_periode_values(self):
        for p in ("1h", "6h", "24h", "7j"):
            assert GetNewsInput(profil="INGENIEUR", periode=p).periode == p

    def test_invalid_periode(self):
        with pytest.raises(ValidationError):
            GetNewsInput(profil="ETUDIANT", periode="3h")


class TestSearchInput:
    def test_valid(self):
        inp = SearchInput(query="python")
        assert inp.query == "python"
        assert inp.page == 1
        assert inp.per_page == 10

    def test_empty_query(self):
        with pytest.raises(ValidationError):
            SearchInput(query="")

    def test_optional_filters(self):
        inp = SearchInput(
            query="rust", domaine="dev", source="hacker_news", profil="INGENIEUR"
        )
        assert inp.domaine == "dev"
        assert inp.source == "hacker_news"

    def test_page_ge_1(self):
        with pytest.raises(ValidationError):
            SearchInput(query="test", page=0)


class TestGetByDomainInput:
    def test_valid(self):
        inp = GetByDomainInput(domaine="ia")
        assert inp.domaine == "ia"
        assert inp.profil is None
        assert inp.nb_articles == 10

    def test_with_profil(self):
        inp = GetByDomainInput(domaine="securite", profil="INGENIEUR")
        assert inp.profil == "INGENIEUR"


class TestGetProfileInput:
    def test_valid(self):
        assert GetProfileInput(profil="ETUDIANT").profil == "ETUDIANT"
        assert GetProfileInput(profil="INGENIEUR").profil == "INGENIEUR"

    def test_invalid(self):
        with pytest.raises(ValidationError):
            GetProfileInput(profil="INCONNU")
