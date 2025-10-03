"""
Performance Benchmarks for Response Compression

Measures:
- Response size reduction
- Compression overhead
- Bandwidth savings
- Compression ratio by content type
- CPU impact
"""

import pytest
import time
import brotli
import gzip
import json
import psutil
from typing import Dict, Any


class CompressionBenchmark:
    """Compression performance benchmarking suite"""

    def __init__(self):
        self.results = {
            "json": {},
            "html": {},
            "text": {},
            "summary": {},
        }

    def generate_json_payload(self, size: str = "medium") -> bytes:
        """Generate JSON test payload"""
        sizes = {
            "small": 100,
            "medium": 1000,
            "large": 10000,
        }

        count = sizes.get(size, 1000)
        data = {
            "items": [
                {
                    "id": i,
                    "name": f"Item {i}",
                    "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                    "metadata": {
                        "created": "2025-10-03T00:00:00Z",
                        "updated": "2025-10-03T00:00:00Z",
                        "tags": ["tag1", "tag2", "tag3"],
                    }
                }
                for i in range(count)
            ]
        }
        return json.dumps(data).encode("utf-8")

    def generate_html_payload(self) -> bytes:
        """Generate HTML test payload"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Page</title>
            <style>
                body { font-family: Arial, sans-serif; }
                .container { max-width: 1200px; margin: 0 auto; }
            </style>
        </head>
        <body>
            <div class="container">
        """

        for i in range(100):
            html += f"""
                <article>
                    <h2>Article {i}</h2>
                    <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                    Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
                </article>
            """

        html += """
            </div>
        </body>
        </html>
        """
        return html.encode("utf-8")

    def generate_text_payload(self) -> bytes:
        """Generate plain text test payload"""
        text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 1000
        return text.encode("utf-8")

    def benchmark_compression(
        self,
        data: bytes,
        method: str,
        level: int,
    ) -> Dict[str, Any]:
        """Benchmark compression for given data and method"""
        # Get CPU usage before
        process = psutil.Process()
        cpu_before = process.cpu_percent()

        # Compress and measure time
        start_time = time.time()

        if method == "brotli":
            compressed = brotli.compress(data, quality=level)
        elif method == "gzip":
            compressed = gzip.compress(data, compresslevel=level)
        else:
            raise ValueError(f"Unknown compression method: {method}")

        compression_time = (time.time() - start_time) * 1000  # ms

        # Get CPU usage after
        cpu_after = process.cpu_percent()
        cpu_delta = cpu_after - cpu_before

        # Calculate metrics
        original_size = len(data)
        compressed_size = len(compressed)
        bytes_saved = original_size - compressed_size
        ratio = (1 - compressed_size / original_size) * 100

        return {
            "method": method,
            "level": level,
            "original_size_bytes": original_size,
            "compressed_size_bytes": compressed_size,
            "bytes_saved": bytes_saved,
            "compression_ratio_percent": round(ratio, 2),
            "compression_time_ms": round(compression_time, 2),
            "cpu_delta_percent": round(cpu_delta, 2),
            "throughput_mb_per_sec": round(
                (original_size / (1024 * 1024)) / (compression_time / 1000), 2
            ),
        }

    def run_benchmarks(self) -> Dict[str, Any]:
        """Run all compression benchmarks"""
        print("\n" + "=" * 80)
        print("COMPRESSION PERFORMANCE BENCHMARK")
        print("=" * 80)

        # JSON Benchmarks
        print("\n[1/3] JSON Response Compression")
        print("-" * 80)
        json_data = self.generate_json_payload("medium")

        json_brotli = self.benchmark_compression(json_data, "brotli", 4)
        json_gzip = self.benchmark_compression(json_data, "gzip", 6)

        self.results["json"] = {
            "brotli": json_brotli,
            "gzip": json_gzip,
        }

        self._print_results("JSON", json_brotli, json_gzip)

        # HTML Benchmarks
        print("\n[2/3] HTML Response Compression")
        print("-" * 80)
        html_data = self.generate_html_payload()

        html_brotli = self.benchmark_compression(html_data, "brotli", 4)
        html_gzip = self.benchmark_compression(html_data, "gzip", 6)

        self.results["html"] = {
            "brotli": html_brotli,
            "gzip": html_gzip,
        }

        self._print_results("HTML", html_brotli, html_gzip)

        # Text Benchmarks
        print("\n[3/3] Text Response Compression")
        print("-" * 80)
        text_data = self.generate_text_payload()

        text_brotli = self.benchmark_compression(text_data, "brotli", 4)
        text_gzip = self.benchmark_compression(text_data, "gzip", 6)

        self.results["text"] = {
            "brotli": text_brotli,
            "gzip": text_gzip,
        }

        self._print_results("Text", text_brotli, text_gzip)

        # Summary
        self._generate_summary()
        self._print_summary()

        return self.results

    def _print_results(self, content_type: str, brotli: Dict, gzip: Dict):
        """Print benchmark results"""
        print(f"\nContent Type: {content_type}")
        print(f"Original Size: {brotli['original_size_bytes']:,} bytes")

        print(f"\nBrotli (level {brotli['level']}):")
        print(f"  Compressed Size: {brotli['compressed_size_bytes']:,} bytes")
        print(f"  Bytes Saved: {brotli['bytes_saved']:,} bytes")
        print(f"  Compression Ratio: {brotli['compression_ratio_percent']}%")
        print(f"  Time: {brotli['compression_time_ms']}ms")
        print(f"  Throughput: {brotli['throughput_mb_per_sec']} MB/s")
        print(f"  CPU Impact: {brotli['cpu_delta_percent']}%")

        print(f"\nGzip (level {gzip['level']}):")
        print(f"  Compressed Size: {gzip['compressed_size_bytes']:,} bytes")
        print(f"  Bytes Saved: {gzip['bytes_saved']:,} bytes")
        print(f"  Compression Ratio: {gzip['compression_ratio_percent']}%")
        print(f"  Time: {gzip['compression_time_ms']}ms")
        print(f"  Throughput: {gzip['throughput_mb_per_sec']} MB/s")
        print(f"  CPU Impact: {gzip['cpu_delta_percent']}%")

        improvement = brotli['compression_ratio_percent'] - gzip['compression_ratio_percent']
        print(f"\nBrotli Advantage: {improvement:+.2f}% better compression ratio")

    def _generate_summary(self):
        """Generate benchmark summary"""
        # Average compression ratios
        brotli_ratios = [
            self.results["json"]["brotli"]["compression_ratio_percent"],
            self.results["html"]["brotli"]["compression_ratio_percent"],
            self.results["text"]["brotli"]["compression_ratio_percent"],
        ]

        gzip_ratios = [
            self.results["json"]["gzip"]["compression_ratio_percent"],
            self.results["html"]["gzip"]["compression_ratio_percent"],
            self.results["text"]["gzip"]["compression_ratio_percent"],
        ]

        # Average times
        brotli_times = [
            self.results["json"]["brotli"]["compression_time_ms"],
            self.results["html"]["brotli"]["compression_time_ms"],
            self.results["text"]["brotli"]["compression_time_ms"],
        ]

        gzip_times = [
            self.results["json"]["gzip"]["compression_time_ms"],
            self.results["html"]["gzip"]["compression_time_ms"],
            self.results["text"]["gzip"]["compression_time_ms"],
        ]

        # Total bytes saved
        total_original = sum([
            self.results["json"]["brotli"]["original_size_bytes"],
            self.results["html"]["brotli"]["original_size_bytes"],
            self.results["text"]["brotli"]["original_size_bytes"],
        ])

        total_brotli_saved = sum([
            self.results["json"]["brotli"]["bytes_saved"],
            self.results["html"]["brotli"]["bytes_saved"],
            self.results["text"]["brotli"]["bytes_saved"],
        ])

        total_gzip_saved = sum([
            self.results["json"]["gzip"]["bytes_saved"],
            self.results["html"]["gzip"]["bytes_saved"],
            self.results["text"]["gzip"]["bytes_saved"],
        ])

        self.results["summary"] = {
            "brotli": {
                "avg_compression_ratio": round(sum(brotli_ratios) / len(brotli_ratios), 2),
                "avg_time_ms": round(sum(brotli_times) / len(brotli_times), 2),
                "total_bytes_saved": total_brotli_saved,
                "bandwidth_savings_percent": round((total_brotli_saved / total_original) * 100, 2),
            },
            "gzip": {
                "avg_compression_ratio": round(sum(gzip_ratios) / len(gzip_ratios), 2),
                "avg_time_ms": round(sum(gzip_times) / len(gzip_times), 2),
                "total_bytes_saved": total_gzip_saved,
                "bandwidth_savings_percent": round((total_gzip_saved / total_original) * 100, 2),
            },
            "total_original_bytes": total_original,
        }

    def _print_summary(self):
        """Print benchmark summary"""
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)

        summary = self.results["summary"]

        print(f"\nTotal Data Tested: {summary['total_original_bytes']:,} bytes")

        print("\nBrotli Performance:")
        print(f"  Average Compression Ratio: {summary['brotli']['avg_compression_ratio']}%")
        print(f"  Average Time: {summary['brotli']['avg_time_ms']}ms")
        print(f"  Total Bytes Saved: {summary['brotli']['total_bytes_saved']:,} bytes")
        print(f"  Bandwidth Savings: {summary['brotli']['bandwidth_savings_percent']}%")

        print("\nGzip Performance:")
        print(f"  Average Compression Ratio: {summary['gzip']['avg_compression_ratio']}%")
        print(f"  Average Time: {summary['gzip']['avg_time_ms']}ms")
        print(f"  Total Bytes Saved: {summary['gzip']['total_bytes_saved']:,} bytes")
        print(f"  Bandwidth Savings: {summary['gzip']['bandwidth_savings_percent']}%")

        print("\nRecommendations:")
        print("  - Use Brotli for modern browsers (better compression)")
        print("  - Fallback to Gzip for universal support")
        print("  - Set minimum size threshold: 500 bytes")
        print("  - Recommended levels: Brotli 4, Gzip 6 (balanced)")

        # Performance targets check
        print("\nPerformance Targets:")
        targets_met = []

        if summary['brotli']['avg_compression_ratio'] >= 60:
            targets_met.append("✓ Compression ratio >60%")
        else:
            targets_met.append("✗ Compression ratio <60%")

        if summary['brotli']['avg_time_ms'] < 10:
            targets_met.append("✓ Compression time <10ms")
        else:
            targets_met.append("✗ Compression time >=10ms")

        if summary['brotli']['bandwidth_savings_percent'] >= 60:
            targets_met.append("✓ Bandwidth savings >60%")
        else:
            targets_met.append("✗ Bandwidth savings <60%")

        for target in targets_met:
            print(f"  {target}")


def test_compression_benchmark():
    """Run compression performance benchmark"""
    benchmark = CompressionBenchmark()
    results = benchmark.run_benchmarks()

    # Verify performance targets
    summary = results["summary"]

    # Target: >60% compression ratio
    assert summary["brotli"]["avg_compression_ratio"] >= 60, \
        f"Brotli compression ratio {summary['brotli']['avg_compression_ratio']}% below target 60%"

    # Target: <10ms compression time
    assert summary["brotli"]["avg_time_ms"] < 10, \
        f"Brotli compression time {summary['brotli']['avg_time_ms']}ms above target 10ms"

    # Target: >60% bandwidth savings
    assert summary["brotli"]["bandwidth_savings_percent"] >= 60, \
        f"Bandwidth savings {summary['brotli']['bandwidth_savings_percent']}% below target 60%"


if __name__ == "__main__":
    # Run benchmark standalone
    benchmark = CompressionBenchmark()
    benchmark.run_benchmarks()
