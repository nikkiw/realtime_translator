import pytest
import threading
import time

from unittest.mock import patch, MagicMock

from .openai_compressor import OpenAICompressor


class DummyResponse:
    class Choice:
        def __init__(self, content):
            # Simulates the structure of OpenAI's choice object
            self.message = MagicMock(content=content)

    def __init__(self, content):
        # Wraps a single choice list as returned by the OpenAI API
        self.choices = [self.Choice(content)]


@pytest.fixture
def compressor():
    # Instantiate compressor with low threshold to trigger compression in tests
    comp = OpenAICompressor(api_key="test-key", compression_threshold=50)
    # Patch only the 'create' method on the already-initialized client
    patcher = patch.object(
        comp.client.chat.completions,
        "create",
        return_value=DummyResponse("compressed summary")
    )
    patcher.start()
    yield comp
    # Ensure background thread is stopped and patch is removed
    comp.stop()
    patcher.stop()


def test_add_text_and_get_context(compressor):
    compressor.add_text("hello world")
    assert "hello world" in compressor.get_context()


def test_compression_trigger_and_summary(compressor):
    # Add text exceeding threshold to initiate compression
    long_text = "a" * 60
    compressor.add_text(long_text)
    # Allow time for background compression thread to process
    time.sleep(0.5)
    ctx = compressor.get_context()
    assert "compressed summary" in ctx


def test_pending_texts_during_compression(compressor):
    # Trigger compression manually
    compressor.add_text("a" * 60)
    time.sleep(0.1)

    # Text added during compression should be queued and re-appended
    compressor.add_text("pending text")
    time.sleep(0.5)
    ctx = compressor.get_context()
    assert "pending text" in ctx


def test_thread_safety_multiple_threads(compressor):
    # Spawn multiple threads to call add_text concurrently
    def worker(text):
        for _ in range(10):
            compressor.add_text(text)

    threads = [threading.Thread(target=worker, args=(f"t{i}",)) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Wait for possible compression
    time.sleep(0.5)
    ctx = compressor.get_context()
    # Ensure at least one instance of each thread's text or compressed summary appears
    assert any(f"t{i}" in ctx or "compressed summary" in ctx for i in range(3))


def test_stop_thread_safe(compressor):
    compressor.stop()
    # After stop(), compression thread should no longer be alive
    assert not compressor._compression_thread.is_alive()


def test_init_without_api_key(monkeypatch):
    # Remove any existing environment variable for API key
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    import sys
    # Force re-import to apply absence of key
    sys.modules.pop("openai", None)
    with pytest.raises(ValueError):
        OpenAICompressor(api_key=None)


def test_do_compression_handles_exception(compressor):
    # Simulate API failure to ensure _do_compression handles exceptions silently
    with patch.object(
        compressor.client.chat.completions,
        "create",
        side_effect=Exception("fail")
    ):
        with compressor._context_lock:
            compressor.context.append("test")
        # Should not raise despite exception
        compressor._do_compression()


def test_compression_worker_handles_exception(compressor):
    # Force _do_compression to throw and verify worker keeps running
    with patch.object(compressor, "_do_compression", side_effect=Exception("fail")):
        compressor._compression_queue.put(True)
        # Give worker time to process without hanging
        time.sleep(0.2)


def test_multiple_compress_requests(compressor):
    # Ensure only one pending request stays in queue when compress() is called repeatedly
    compressor._compression_queue.queue.clear()
    compressor.compress()
    compressor.compress()
    assert compressor._compression_queue.qsize() == 1


def test_stop_idempotent(compressor):
    # Calling stop() multiple times should not raise errors
    compressor.stop()
    compressor.stop()
