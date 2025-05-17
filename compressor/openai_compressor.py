import os
from typing import List
from openai import OpenAI
from compressor import BaseCompressor
import threading
from queue import Queue, Empty


class OpenAICompressor(BaseCompressor):
    """
    Concrete compressor using OpenAI to intelligently shrink context.
    Leverages GPT to generate concise summaries of past conversations.
    """

    def __init__(
        self,
        api_key: str | None = None,
        compression_threshold: int = 1500
    ):
        super().__init__(compression_threshold)
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OpenAI API key must be provided")

        self.client = OpenAI(api_key=api_key)
        # Lock for protecting access to the shared context buffer
        self._context_lock = threading.Lock()
        # Lock for protecting the list of texts pending to be added during compression
        self._pending_texts_lock = threading.Lock()
        # Single-slot queue: a new compression request will overwrite any existing one
        self._compression_queue: Queue[bool] = Queue(maxsize=1)
        # Event flag indicating compression is in progress
        self._compress_event = threading.Event()
        self._pending_texts: List[str] = []
        # Event flag to signal the compression thread to exit
        self._should_stop = threading.Event()
        # Worker thread will run compression tasks in the background
        self._compression_thread = threading.Thread(
            target=self._compression_worker,
            daemon=True
        )
        self._compression_thread.start()

    def add_text(self, text: str | list[str]) -> None:
        """
        Thread-safe addition of new text into the context buffer.
        If compression is active, enqueue to pending list instead.
        """
        if isinstance(text, list):
            text = "\n ".join(text)

        if self._compress_event.is_set():
            # If compressing, defer appends to the pending bucket
            with self._pending_texts_lock:
                self._pending_texts.append(text)
        else:
            # Otherwise, add directly to the primary context under lock
            with self._context_lock:
                super().add_text(text)

    def _compression_worker(self) -> None:
        """
        Background worker that listens for compression triggers.
        """
        while not self._should_stop.is_set():
            try:
                # Wait up to 0.5s for a compression request; loop if none arrive
                if not self._compression_queue.get(timeout=0.5):
                    continue

                # Mark that we are in compression phase
                self._compress_event.set()
                self._do_compression()
            except Empty:
                continue
            except Exception as e:
                # Print error so worker can continue handling future tasks
                print(f"Error in compression worker: {e}")
            finally:
                # Clear flag even if an error occurred
                self._compress_event.clear()

    def stop(self):
        """Safely stops the background compression thread."""
        self._should_stop.set()
        if self._compression_thread.is_alive():
            self._compression_thread.join(timeout=1.0)

    def _do_compression(self) -> None:
        """
        Performs the actual summarization by calling the OpenAI API.
        """
        try:
            # Snapshot and clear current context under lock
            with self._context_lock:
                if not self.context:
                    return
                text_to_compress = "\n".join(self.context)

            # Construct summarization prompt
            prompt = (
                "Please produce a concise summary of the following conversation, "
                "presenting only the core storyline first, then adding supporting details. "
                "The input is a transcription of speech from an online recording. "
                "Retain all main themes and key points, and make the summary approximately "
                "one quarter of the original length:\n\n"
                f"{text_to_compress}"
            )

            # Issue API call outside of locks to avoid blocking add_text()
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=int(self.compression_threshold * 1.2 + 1),
                temperature=0.2
            )

            # Merge summary and any texts accumulated during compression
            with self._context_lock:
                choice = response.choices[0].message.content if response.choices else ""
                if choice:
                    # Only clear context if we got a valid summary back
                    self.context.clear()
                    self.context.append(choice)

                # Append any pending texts that arrived mid-compression
                with self._pending_texts_lock:
                    if self._pending_texts:
                        self.context.extend(self._pending_texts)
                        self._pending_texts.clear()

                # Recompute size after update
                self.current_size = sum(len(t) for t in self.context)

        except Exception as e:
            print(f"Error during compression: {e}")

    def compress(self) -> None:
        """
        Enqueue a compression request, dropping any previous pending request.
        """
        try:
            self._compression_queue.get_nowait()
        except Empty:
            pass
        # New request will signal the worker to run
        self._compression_queue.put(True)

    def get_context(self) -> str:
        """
        Returns the full available context string.
        Includes pending texts if compression is ongoing.
        """
        if self._compress_event.is_set():
            # Merge both lists under both locks to give up-to-date view
            with self._context_lock, self._pending_texts_lock:
                return " ".join(self.context + self._pending_texts)
        else:
            with self._context_lock:
                return " ".join(self.context)
