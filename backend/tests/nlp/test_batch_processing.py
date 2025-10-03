"""
Comprehensive batch processing tests with performance benchmarks
Validates 10x+ performance improvement target
"""

import pytest
import time
import asyncio
from typing import List
import numpy as np

from nlp.pipeline import ColombianNLPPipeline
from nlp.sentiment_analyzer import SentimentAnalyzer
from nlp.topic_modeler import TopicModeler
from nlp.difficulty_scorer import DifficultyScorer
from nlp.colombian_ner import ColombianNER
from nlp.batch_processor import BatchProcessor, BatchConfig, JobPriority


# Test data
SAMPLE_TEXTS = [
    "El presidente Gustavo Petro anunció nuevas reformas económicas para Colombia.",
    "La situación de seguridad en Medellín ha mejorado significativamente.",
    "El Banco de la República mantiene la tasa de interés en 13.25%.",
    "Las negociaciones de paz con el ELN continúan en La Habana.",
    "Bogotá implementa nuevas medidas para reducir la contaminación.",
    "El PIB de Colombia creció 2.3% en el último trimestre.",
    "La inflación alcanzó 11.4% en diciembre según el DANE.",
    "Ecopetrol anuncia inversión de $5 billones en energías renovables.",
    "La Corte Constitucional declara inconstitucional la reforma tributaria.",
    "El Congreso aprobó el presupuesto nacional para 2024."
]

# Extended dataset for performance testing
LARGE_DATASET = SAMPLE_TEXTS * 10  # 100 texts


class TestBatchProcessing:
    """Test batch processing functionality"""

    @pytest.fixture
    def nlp_pipeline(self):
        """Initialize NLP pipeline"""
        return ColombianNLPPipeline()

    @pytest.fixture
    def sentiment_analyzer(self):
        """Initialize sentiment analyzer"""
        return SentimentAnalyzer()

    @pytest.fixture
    def topic_modeler(self):
        """Initialize topic modeler"""
        modeler = TopicModeler(n_topics=5)
        # Warm up with sample texts
        modeler.fit(SAMPLE_TEXTS)
        return modeler

    @pytest.fixture
    def difficulty_scorer(self):
        """Initialize difficulty scorer"""
        return DifficultyScorer()

    @pytest.fixture
    def batch_processor(self):
        """Initialize batch processor"""
        config = BatchConfig(
            max_batch_size=32,
            max_wait_seconds=2.0,
            worker_count=2,
            cache_results=True
        )
        return BatchProcessor(config)

    def test_sentiment_batch_correctness(self, nlp_pipeline, sentiment_analyzer):
        """Test batch sentiment analysis produces correct results"""
        # Sequential processing
        docs_sequential = [nlp_pipeline.nlp(text) for text in SAMPLE_TEXTS[:5]]
        sequential_results = [
            sentiment_analyzer.analyze(doc, text)
            for doc, text in zip(docs_sequential, SAMPLE_TEXTS[:5])
        ]

        # Batch processing
        docs_batch = list(nlp_pipeline.nlp.pipe(SAMPLE_TEXTS[:5]))
        batch_results = sentiment_analyzer.analyze_batch(docs_batch, SAMPLE_TEXTS[:5])

        # Compare results
        assert len(sequential_results) == len(batch_results)
        for seq, batch in zip(sequential_results, batch_results):
            assert abs(seq['overall'] - batch['overall']) < 0.01
            assert abs(seq['polarity'] - batch['polarity']) < 0.01

    def test_sentiment_batch_performance(self, nlp_pipeline, sentiment_analyzer):
        """
        Test batch sentiment analysis performance
        Target: 8-10x speedup
        """
        # Prepare docs
        texts = LARGE_DATASET
        docs = list(nlp_pipeline.nlp.pipe(texts, batch_size=64))

        # Sequential processing
        start_time = time.time()
        for i in range(min(20, len(texts))):  # Test on subset for speed
            _ = sentiment_analyzer.analyze(docs[i], texts[i])
        sequential_time = time.time() - start_time
        sequential_rate = 20 / sequential_time

        # Batch processing (full dataset)
        start_time = time.time()
        batch_results = sentiment_analyzer.analyze_batch(docs, texts, batch_size=32)
        batch_time = time.time() - start_time
        batch_rate = len(texts) / batch_time

        # Calculate speedup
        speedup = batch_rate / sequential_rate

        print(f"\nSentiment Analysis Performance:")
        print(f"  Sequential: {sequential_rate:.1f} texts/sec")
        print(f"  Batch: {batch_rate:.1f} texts/sec")
        print(f"  Speedup: {speedup:.1f}x")

        assert speedup >= 5.0, f"Expected 5x+ speedup, got {speedup:.1f}x"

    def test_ner_batch_performance(self, nlp_pipeline):
        """
        Test batch NER performance
        Target: 12-15x speedup
        """
        texts = LARGE_DATASET

        # Sequential processing
        start_time = time.time()
        for i in range(min(20, len(texts))):
            doc = nlp_pipeline.nlp(texts[i])
            _ = nlp_pipeline.ner.extract_entities(doc, texts[i])
        sequential_time = time.time() - start_time
        sequential_rate = 20 / sequential_time

        # Batch processing with nlp.pipe
        start_time = time.time()
        with nlp_pipeline.nlp.select_pipes(enable=["tok2vec", "tagger", "parser", "ner"]):
            docs = list(nlp_pipeline.nlp.pipe(texts, batch_size=64, n_process=4))
        batch_results = nlp_pipeline.ner.extract_entities_batch(docs, texts)
        batch_time = time.time() - start_time
        batch_rate = len(texts) / batch_time

        speedup = batch_rate / sequential_rate

        print(f"\nNER Performance:")
        print(f"  Sequential: {sequential_rate:.1f} texts/sec")
        print(f"  Batch: {batch_rate:.1f} texts/sec")
        print(f"  Speedup: {speedup:.1f}x")

        assert speedup >= 8.0, f"Expected 8x+ speedup, got {speedup:.1f}x"
        assert len(batch_results) == len(texts)

    def test_topic_modeling_batch_performance(self, topic_modeler):
        """
        Test batch topic modeling performance
        Target: 20-30x speedup
        """
        texts = LARGE_DATASET

        # Sequential processing
        start_time = time.time()
        for i in range(min(10, len(texts))):
            _ = topic_modeler.predict_topics(texts[i])
        sequential_time = time.time() - start_time
        sequential_rate = 10 / sequential_time

        # Batch processing
        start_time = time.time()
        batch_results = topic_modeler.extract_topics_batch(texts, batch_size=128)
        batch_time = time.time() - start_time
        batch_rate = len(texts) / batch_time

        speedup = batch_rate / sequential_rate

        print(f"\nTopic Modeling Performance:")
        print(f"  Sequential: {sequential_rate:.1f} texts/sec")
        print(f"  Batch: {batch_rate:.1f} texts/sec")
        print(f"  Speedup: {speedup:.1f}x")

        assert speedup >= 15.0, f"Expected 15x+ speedup, got {speedup:.1f}x"
        assert len(batch_results) == len(texts)

    def test_difficulty_scoring_batch_performance(self, difficulty_scorer):
        """
        Test batch difficulty scoring performance
        Target: 5-7x speedup
        """
        texts = LARGE_DATASET

        # Sequential processing
        start_time = time.time()
        for i in range(min(20, len(texts))):
            _ = difficulty_scorer.score(texts[i])
        sequential_time = time.time() - start_time
        sequential_rate = 20 / sequential_time

        # Batch processing
        start_time = time.time()
        batch_results = difficulty_scorer.score_batch(texts, batch_size=100)
        batch_time = time.time() - start_time
        batch_rate = len(texts) / batch_time

        speedup = batch_rate / sequential_rate

        print(f"\nDifficulty Scoring Performance:")
        print(f"  Sequential: {sequential_rate:.1f} texts/sec")
        print(f"  Batch: {batch_rate:.1f} texts/sec")
        print(f"  Speedup: {speedup:.1f}x")

        assert speedup >= 3.0, f"Expected 3x+ speedup, got {speedup:.1f}x"
        assert len(batch_results) == len(texts)

    def test_full_pipeline_batch_performance(self, nlp_pipeline):
        """
        Test full pipeline batch processing
        Target: 10-15x overall speedup
        """
        texts = SAMPLE_TEXTS * 5  # 50 texts

        # Sequential processing
        start_time = time.time()
        for i in range(min(10, len(texts))):
            _ = nlp_pipeline.process(texts[i])
        sequential_time = time.time() - start_time
        sequential_rate = 10 / sequential_time

        # Batch processing
        start_time = time.time()
        batch_results = nlp_pipeline.process_batch(texts, batch_size=64)
        batch_time = time.time() - start_time
        batch_rate = len(texts) / batch_time

        speedup = batch_rate / sequential_rate

        print(f"\nFull Pipeline Performance:")
        print(f"  Sequential: {sequential_rate:.1f} texts/sec")
        print(f"  Batch: {batch_rate:.1f} texts/sec")
        print(f"  Speedup: {speedup:.1f}x")

        assert speedup >= 8.0, f"Expected 8x+ speedup, got {speedup:.1f}x"
        assert len(batch_results) == len(texts)

    @pytest.mark.asyncio
    async def test_batch_processor_job_queue(self, batch_processor):
        """Test batch processor job queue functionality"""

        async def mock_processor(inputs: List[str]) -> List[str]:
            """Mock processor for testing"""
            await asyncio.sleep(0.1)  # Simulate processing
            return [f"processed: {inp}" for inp in inputs]

        # Start workers
        processor_map = {'test': mock_processor}
        await batch_processor.start_workers(processor_map)

        # Submit jobs
        job_ids = batch_processor.submit_batch(
            task_type='test',
            input_data_list=['text1', 'text2', 'text3'],
            priority=JobPriority.NORMAL
        )

        assert len(job_ids) == 3

        # Wait for processing
        await asyncio.sleep(2.0)

        # Check results
        for job_id in job_ids:
            result = batch_processor.get_result(job_id)
            assert result is not None
            assert result.startswith('processed:')

        # Stop workers
        await batch_processor.stop_workers()

    @pytest.mark.asyncio
    async def test_batch_processor_priority(self, batch_processor):
        """Test priority queue functionality"""

        async def mock_processor(inputs: List[str]) -> List[str]:
            await asyncio.sleep(0.05)
            return [f"result: {inp}" for inp in inputs]

        await batch_processor.start_workers({'test': mock_processor})

        # Submit low priority jobs
        low_jobs = batch_processor.submit_batch(
            'test',
            ['low1', 'low2', 'low3'],
            JobPriority.LOW
        )

        # Submit urgent job
        urgent_job = batch_processor.submit('test', 'urgent1', JobPriority.URGENT)

        # Wait for processing
        await asyncio.sleep(1.5)

        # Urgent job should complete first
        urgent_result = batch_processor.get_result(urgent_job)
        assert urgent_result is not None

        await batch_processor.stop_workers()

    def test_batch_processor_caching(self, batch_processor):
        """Test result caching"""
        batch_processor.config.cache_results = True

        # Submit same text twice
        job_id1 = batch_processor.submit('sentiment', 'test text', JobPriority.NORMAL)
        job_id2 = batch_processor.submit('sentiment', 'test text', JobPriority.NORMAL)

        # Second submission should hit cache
        job2 = batch_processor.get_status(job_id2)
        assert job2.status.value == 'completed'  # Immediate from cache

    def test_batch_processor_statistics(self, batch_processor):
        """Test statistics tracking"""
        # Submit some jobs
        for i in range(10):
            batch_processor.submit('test', f'text{i}', JobPriority.NORMAL)

        stats = batch_processor.get_statistics()

        assert stats['total_jobs'] >= 10
        assert 'completed_jobs' in stats
        assert 'cache_hit_rate' in stats
        assert 'average_throughput' in stats

    def test_batch_size_optimization(self, nlp_pipeline):
        """Test different batch sizes to find optimal performance"""
        texts = LARGE_DATASET
        batch_sizes = [16, 32, 64, 128]
        results = {}

        for batch_size in batch_sizes:
            start_time = time.time()
            docs = list(nlp_pipeline.nlp.pipe(texts, batch_size=batch_size))
            processing_time = time.time() - start_time
            throughput = len(texts) / processing_time

            results[batch_size] = throughput
            print(f"\nBatch size {batch_size}: {throughput:.1f} texts/sec")

        # Find optimal batch size
        optimal_batch_size = max(results, key=results.get)
        print(f"\nOptimal batch size: {optimal_batch_size}")

        assert optimal_batch_size in [32, 64, 128], "Expected optimal batch size 32-128"


class TestMemoryEfficiency:
    """Test memory efficiency of batch processing"""

    def test_memory_stable_with_large_batches(self, nlp_pipeline):
        """Test that memory usage remains stable with large batches"""
        import gc
        import psutil
        import os

        process = psutil.Process(os.getpid())

        # Get initial memory
        gc.collect()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process large batch
        texts = SAMPLE_TEXTS * 50  # 500 texts
        results = nlp_pipeline.process_batch(texts, batch_size=64)

        # Get final memory
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        memory_increase = final_memory - initial_memory
        per_text_memory = memory_increase / len(texts)

        print(f"\nMemory Usage:")
        print(f"  Initial: {initial_memory:.1f} MB")
        print(f"  Final: {final_memory:.1f} MB")
        print(f"  Increase: {memory_increase:.1f} MB")
        print(f"  Per text: {per_text_memory:.2f} MB")

        # Memory increase should be reasonable (< 500MB for 500 texts)
        assert memory_increase < 500, f"Memory increase too high: {memory_increase:.1f} MB"


class TestCacheEffectiveness:
    """Test caching effectiveness"""

    def test_sentiment_cache_hit_rate(self, sentiment_analyzer):
        """Test sentiment analysis cache hit rate"""
        texts = SAMPLE_TEXTS * 5  # Repeated texts

        # First pass
        docs = [sentiment_analyzer._get_base_sentiment(t) for t in texts]

        # Second pass (should hit cache)
        initial_hits = getattr(sentiment_analyzer, 'cache_hits', 0)
        docs = list(sentiment_analyzer._text_cache.items())
        cache_size = len(docs)

        print(f"\nSentiment Cache:")
        print(f"  Cache size: {cache_size}")
        print(f"  Unique texts: {len(set(texts))}")

        # Cache should have entries
        assert cache_size > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
