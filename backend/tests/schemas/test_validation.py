"""
Comprehensive validation tests for all Pydantic schemas
Tests valid inputs, invalid inputs, edge cases, and security patterns
"""

import pytest
from pydantic import ValidationError
from datetime import datetime, timedelta

from app.schemas.auth_schemas import (
    UserRegister, UserLogin, UserUpdate, PasswordReset, PasswordUpdate
)
from app.schemas.common_schemas import (
    PaginationParams, SearchQuery, DateRangeFilter, SortParams
)
from app.schemas.scraping_schemas import (
    ScrapingRequest, SourceFilter, ContentFilter
)
from app.schemas.analysis_schemas import (
    AnalysisRequest, BatchAnalysisRequest, AnalysisType
)
from app.schemas.language_schemas import (
    VocabularyWordRequest, PracticeSessionRequest, PracticeResultRequest, CEFRLevel
)


class TestAuthSchemas:
    """Test authentication schema validation"""

    def test_user_register_valid(self):
        """Test valid user registration"""
        data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Juan García",
            "preferred_language": "es"
        }
        user = UserRegister(**data)
        assert user.email == "test@example.com"
        assert user.full_name == "Juan García"

    def test_user_register_weak_password(self):
        """Test password strength validation"""
        # No uppercase
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="weakpass123!",
                full_name="Test User"
            )
        assert "uppercase" in str(exc_info.value).lower()

        # No lowercase
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="WEAKPASS123!",
                full_name="Test User"
            )
        assert "lowercase" in str(exc_info.value).lower()

        # No number
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="WeakPassword!",
                full_name="Test User"
            )
        assert "number" in str(exc_info.value).lower()

        # No special character
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="WeakPass123",
                full_name="Test User"
            )
        assert "special" in str(exc_info.value).lower()

        # Too short
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="Weak1!",
                full_name="Test User"
            )
        assert "8 characters" in str(exc_info.value).lower()

    def test_user_register_invalid_email(self):
        """Test email validation"""
        with pytest.raises(ValidationError):
            UserRegister(
                email="invalid-email",
                password="SecurePass123!",
                full_name="Test User"
            )

    def test_user_register_invalid_name(self):
        """Test name validation"""
        # Special characters not allowed (except hyphen and apostrophe)
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="SecurePass123!",
                full_name="Test<script>alert(1)</script>User"
            )
        assert "invalid characters" in str(exc_info.value).lower()

    def test_user_update_valid(self):
        """Test valid user update"""
        data = {"full_name": "Updated Name", "preferred_language": "en"}
        update = UserUpdate(**data)
        assert update.full_name == "Updated Name"

    def test_password_update_validation(self):
        """Test password update validation"""
        valid_data = {
            "token": "a" * 50,  # Valid token
            "new_password": "NewSecure123!"
        }
        update = PasswordUpdate(**valid_data)
        assert update.new_password == "NewSecure123!"

        # Weak password
        with pytest.raises(ValidationError):
            PasswordUpdate(token="a" * 50, new_password="weak")


class TestCommonSchemas:
    """Test common schema validation"""

    def test_pagination_valid(self):
        """Test valid pagination parameters"""
        pagination = PaginationParams(skip=0, limit=20)
        assert pagination.skip == 0
        assert pagination.limit == 20

    def test_pagination_invalid_limits(self):
        """Test pagination limit validation"""
        # Negative skip
        with pytest.raises(ValidationError):
            PaginationParams(skip=-1, limit=20)

        # Limit too large
        with pytest.raises(ValidationError):
            PaginationParams(skip=0, limit=101)

        # Limit too small
        with pytest.raises(ValidationError):
            PaginationParams(skip=0, limit=0)

    def test_search_query_sql_injection(self):
        """Test SQL injection prevention"""
        # Test common SQL injection patterns
        malicious_queries = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--",
            "'; EXEC xp_cmdshell('dir')--"
        ]

        for query in malicious_queries:
            with pytest.raises(ValidationError) as exc_info:
                SearchQuery(query=query)
            error_msg = str(exc_info.value).lower()
            assert "forbidden" in error_msg or "pattern" in error_msg

    def test_search_query_valid(self):
        """Test valid search queries"""
        query = SearchQuery(query="Colombian politics analysis")
        assert query.query == "Colombian politics analysis"

        # Test whitespace normalization
        query = SearchQuery(query="multiple    spaces    test")
        assert query.query == "multiple spaces test"

    def test_date_range_validation(self):
        """Test date range validation"""
        # Valid date range
        now = datetime.utcnow()
        past = now - timedelta(days=7)
        date_range = DateRangeFilter(start_date=past, end_date=now)
        assert date_range.start_date < date_range.end_date

        # Future date not allowed
        future = now + timedelta(days=1)
        with pytest.raises(ValidationError) as exc_info:
            DateRangeFilter(start_date=future)
        assert "future" in str(exc_info.value).lower()

        # End before start
        with pytest.raises(ValidationError) as exc_info:
            DateRangeFilter(start_date=now, end_date=past)
        assert "after" in str(exc_info.value).lower()

    def test_sort_params_validation(self):
        """Test sort parameter validation"""
        # Valid sort
        sort = SortParams(sort_by="created_at", sort_order="desc")
        assert sort.sort_order == "desc"

        # Invalid sort order
        with pytest.raises(ValidationError):
            SortParams(sort_by="created_at", sort_order="invalid")

        # SQL injection in sort field
        with pytest.raises(ValidationError):
            SortParams(sort_by="id; DROP TABLE users", sort_order="asc")


class TestScrapingSchemas:
    """Test scraping schema validation"""

    def test_scraping_request_valid(self):
        """Test valid scraping request"""
        request = ScrapingRequest(source_name="El Tiempo", force_refresh=True)
        assert request.source_name == "El Tiempo"
        assert request.force_refresh is True

    def test_scraping_request_path_traversal(self):
        """Test path traversal prevention"""
        with pytest.raises(ValidationError) as exc_info:
            ScrapingRequest(source_name="../etc/passwd")
        assert "invalid" in str(exc_info.value).lower()

        with pytest.raises(ValidationError):
            ScrapingRequest(source_name="..\\windows\\system32")

    def test_content_filter_valid(self):
        """Test valid content filtering"""
        filter_params = ContentFilter(
            source="El Tiempo",
            category="politics",
            min_difficulty=0.3,
            max_difficulty=0.7,
            skip=0,
            limit=20
        )
        assert filter_params.source == "El Tiempo"
        assert filter_params.min_difficulty == 0.3

    def test_content_filter_difficulty_range(self):
        """Test difficulty score validation"""
        # Invalid range (min > max not validated at field level, but should be checked in business logic)
        filter_params = ContentFilter(min_difficulty=0.8, max_difficulty=0.3)
        # This is allowed at schema level, business logic should validate

        # Out of range
        with pytest.raises(ValidationError):
            ContentFilter(min_difficulty=-0.1)

        with pytest.raises(ValidationError):
            ContentFilter(max_difficulty=1.1)

    def test_content_filter_sql_injection(self):
        """Test SQL injection in search query"""
        with pytest.raises(ValidationError) as exc_info:
            ContentFilter(search_query="'; DROP TABLE content--")
        assert "forbidden" in str(exc_info.value).lower()

    def test_source_filter_enums(self):
        """Test source filter enum validation"""
        from app.schemas.scraping_schemas import SourceCategory, SourcePriority

        valid_filter = SourceFilter(
            category=SourceCategory.MEDIA,
            priority=SourcePriority.HIGH
        )
        assert valid_filter.category == "media"

        # Invalid category
        with pytest.raises(ValidationError):
            SourceFilter(category="invalid_category")


class TestAnalysisSchemas:
    """Test analysis schema validation"""

    def test_analysis_request_valid(self):
        """Test valid analysis request"""
        request = AnalysisRequest(
            text="El Congreso de Colombia aprobó una nueva reforma política.",
            analysis_types=[AnalysisType.SENTIMENT, AnalysisType.ENTITIES],
            language="es"
        )
        assert len(request.analysis_types) == 2

    def test_analysis_request_text_length(self):
        """Test text length validation"""
        # Too short
        with pytest.raises(ValidationError):
            AnalysisRequest(text="Short")

        # Too long
        with pytest.raises(ValidationError):
            AnalysisRequest(text="a" * 50001)

    def test_analysis_request_xss_prevention(self):
        """Test XSS attack prevention"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert(1)",
            "<img src=x onerror=alert(1)>",
            "<body onload=alert(1)>"
        ]

        for payload in xss_payloads:
            with pytest.raises(ValidationError) as exc_info:
                AnalysisRequest(text=payload + " " + "a" * 20)  # Make it long enough
            assert "malicious" in str(exc_info.value).lower()

    def test_batch_analysis_request_valid(self):
        """Test valid batch analysis request"""
        request = BatchAnalysisRequest(
            content_ids=[1, 2, 3, 4, 5],
            analysis_types=[AnalysisType.SENTIMENT]
        )
        assert len(request.content_ids) == 5

    def test_batch_analysis_limits(self):
        """Test batch analysis limits"""
        # Too many IDs
        with pytest.raises(ValidationError) as exc_info:
            BatchAnalysisRequest(content_ids=list(range(1, 102)))
        assert "100" in str(exc_info.value)

        # Empty list
        with pytest.raises(ValidationError):
            BatchAnalysisRequest(content_ids=[])

    def test_batch_analysis_deduplication(self):
        """Test duplicate ID removal"""
        request = BatchAnalysisRequest(content_ids=[1, 2, 2, 3, 3, 3])
        assert len(request.content_ids) == 3
        assert set(request.content_ids) == {1, 2, 3}

    def test_analysis_type_expansion(self):
        """Test 'all' analysis type expansion"""
        request = AnalysisRequest(
            text="Test text for analysis validation.",
            analysis_types=[AnalysisType.ALL]
        )
        # Should expand to all analysis types
        expected_types = [
            AnalysisType.SENTIMENT,
            AnalysisType.ENTITIES,
            AnalysisType.TOPICS,
            AnalysisType.DIFFICULTY,
            AnalysisType.SUMMARY
        ]
        assert set(request.analysis_types) == set(expected_types)


class TestLanguageSchemas:
    """Test language learning schema validation"""

    def test_vocabulary_word_request_valid(self):
        """Test valid vocabulary word request"""
        request = VocabularyWordRequest(
            word="aprender",
            translation="to learn",
            difficulty_level=CEFRLevel.A1,
            example_sentence="Me gusta aprender español."
        )
        assert request.word == "aprender"
        assert request.difficulty_level == "A1"

    def test_vocabulary_word_sanitization(self):
        """Test text sanitization"""
        # XSS attempt
        with pytest.raises(ValidationError) as exc_info:
            VocabularyWordRequest(
                word="test",
                translation="<script>alert(1)</script>",
                example_sentence="Example sentence"
            )
        assert "malicious" in str(exc_info.value).lower()

        # Invalid characters
        with pytest.raises(ValidationError):
            VocabularyWordRequest(
                word="test<>{}",
                translation="to test"
            )

    def test_practice_session_request_valid(self):
        """Test valid practice session request"""
        request = PracticeSessionRequest(
            category_id=1,
            difficulty_level=CEFRLevel.A2,
            num_words=15,
            practice_type="flashcard"
        )
        assert request.num_words == 15

    def test_practice_session_word_limits(self):
        """Test word count limits"""
        # Too few
        with pytest.raises(ValidationError):
            PracticeSessionRequest(num_words=0)

        # Too many
        with pytest.raises(ValidationError):
            PracticeSessionRequest(num_words=51)

    def test_practice_result_request_valid(self):
        """Test valid practice result"""
        request = PracticeResultRequest(
            word_id=1,
            correct=True,
            response_time=3.5,
            practice_type="flashcard"
        )
        assert request.correct is True
        assert request.response_time == 3.5

    def test_practice_result_response_time(self):
        """Test response time validation"""
        # Too short (unrealistic)
        with pytest.raises(ValidationError) as exc_info:
            PracticeResultRequest(
                word_id=1,
                correct=True,
                response_time=0.05,
                practice_type="flashcard"
            )
        assert "too short" in str(exc_info.value).lower()

        # Too long (over 5 minutes)
        with pytest.raises(ValidationError) as exc_info:
            PracticeResultRequest(
                word_id=1,
                correct=True,
                response_time=301,
                practice_type="flashcard"
            )
        assert "maximum" in str(exc_info.value).lower()


class TestSecurityPatterns:
    """Test security-specific validation patterns"""

    def test_email_max_length(self):
        """Test email length limit"""
        long_email = "a" * 250 + "@example.com"
        with pytest.raises(ValidationError):
            UserRegister(
                email=long_email,
                password="SecurePass123!",
                full_name="Test User"
            )

    def test_password_max_length(self):
        """Test password length limit"""
        long_password = "A1!" + "a" * 200
        with pytest.raises(ValidationError):
            UserRegister(
                email="test@example.com",
                password=long_password,
                full_name="Test User"
            )

    def test_null_byte_injection(self):
        """Test null byte injection prevention"""
        with pytest.raises(ValidationError):
            AnalysisRequest(text="Normal text\x00with null byte")

    def test_unicode_validation(self):
        """Test Unicode character handling"""
        # Valid Unicode (Spanish characters)
        request = VocabularyWordRequest(
            word="niño",
            translation="child"
        )
        assert request.word == "niño"

        user = UserRegister(
            email="test@example.com",
            password="SecurePass123!",
            full_name="José García"
        )
        assert user.full_name == "José García"

    def test_whitespace_normalization(self):
        """Test excessive whitespace handling"""
        # Multiple spaces should be normalized
        query = SearchQuery(query="multiple    spaces    test")
        assert "  " not in query.query

        user = UserRegister(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Juan    Carlos    García"
        )
        assert "  " not in user.full_name


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_empty_optional_fields(self):
        """Test optional fields can be None"""
        filter_params = ContentFilter()
        assert filter_params.source is None
        assert filter_params.category is None

    def test_default_values(self):
        """Test default values are applied"""
        pagination = PaginationParams()
        assert pagination.skip == 0
        assert pagination.limit == 20

        request = AnalysisRequest(text="Test text for default analysis.")
        assert "es" == request.language

    def test_boundary_values(self):
        """Test boundary value validation"""
        # Difficulty scores at boundaries
        filter_params = ContentFilter(min_difficulty=0.0, max_difficulty=1.0)
        assert filter_params.min_difficulty == 0.0
        assert filter_params.max_difficulty == 1.0

        # Pagination at boundaries
        pagination = PaginationParams(skip=0, limit=1)
        assert pagination.limit == 1

        pagination = PaginationParams(skip=10000, limit=100)
        assert pagination.skip == 10000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
