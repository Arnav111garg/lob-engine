## Parser Responsibilities (What It Should and Should Not Do)

> A parser acts strictly as the boundary layer between the raw byte network protocol and the application domain.

* What it SHOULD do:
   * Byte Stream Unpacking: Read raw bytes according to the protocol specification (e.g., reading 2 bytes for length, 1 byte for type, 8 bytes for reference ID).
   * Endianness Conversion: Translate Big-Endian network bytes into Native Little-Endian CPU integers.
   * Scale Application: Divide integer price fields by the protocol factor (eg., divide by $10,000$ to format decimal values).
   * Message Validation: Verify payload lengths and ensure messages are well-formed.
   * Event Emission: Convert raw structures into clean event payloads (AddOrder, CancelOrder) and dispatch them down the pipeline.

* What it SHOULD NOT do:
   * State Management: It must never maintain order book state, track active price levels, or store execution queues.
   * Business Logic: It must not match orders, validate whether an order ID exists before deletion, or check if a trader has sufficient funds.
   * I/O & Persistence: It must not handle file writing, database insertions, or disk flushing, its sole focus is parsing stream data.

## Streaming Architecture (Why We Avoid Loading the Entire File)

> High-frequency market data files (like Nasdaq ITCH 5.0) are uncompressed 9 GB to 15+ GB per day containing hundreds of millions of messages.

> Loading the entire file into memory (e.g., using pandas.read_csv or loading all bytes into RAM at once) causes severe architectural failures:

1. 1. Memory Exhaustion (Out-Of-Memory Crash): A 10 GB file uncompressed in Python DataFrames or object trees expands by 3x–5x due to object overhead, causing process crashes.
2. 2. High Cache Invalidation (L1/L2/L3 CPU Misses): Processors run fastest when processing small chunks of data that fit inside CPU caches ($32\text{ KB}$ to $32\text{ MB}$). Streaming processes data in cache-friendly micro-batches.
3. 3. Latency Inflation: Pre-loading forces the user to wait minutes for the full file to load before performing any calculations. A streaming pipeline starts emitting real-time event updates within microseconds of reading the first byte.

## Message Lifecycle
> Every binary message passes through a deterministic 5-step lifecycle:

[Read Length] ➔ [Read Body] ➔ [Determine Type] ➔ [Decode] ➔ [Emit Event]

1. Read Length: Read the fixed header offset (e.g., the first 2 bytes) to extract an unsigned integer indicating the size $N$ of the upcoming message payload.

2. Read Body: Read exactly $N - 1$ bytes (or $N$ bytes) from the file/stream buffer into an isolated byte array.
3. Determine Type: Inspect the message_type byte (e.g., the 1st byte of the body, such as ASCII 'A' for Add Order or 'E' for Execution).
4. Decode: Unpack the byte buffer using the corresponding format string (e.g., Python struct.unpack('>HH6sQ1sI8sI')) to extract integers, strings, and timestamps.
5. Emit Event: Instantiate a structured event dataclass/namedtuple and pass it to downstream handlers or matching engine listeners.

## Dispatch Table Design (Why It Scales Better Than if/elif Chains)
> Instead of using a long chain of conditions:
###### SLOW & UNMAINTAINABLE:
if msg_type == 'A':
    handle_add(data)
elif msg_type == 'E':
    handle_exec(data)
elif msg_type == 'D':
    handle_delete(data)
###### ... 20+ more elif blocks


> A Dispatch Table maps message keys directly to their decoding functions using a Hash Map/Dictionary:
###### FAST & SCALABLE (O(1) Lookup):
DISPATCH_TABLE = {
    'A': parse_add_order,
    'E': parse_execute_order,
    'D': parse_delete_order,
    'U': parse_replace_order}

###### Execution:
handler = DISPATCH_TABLE.get(msg_type)
if handler:
    event = handler(message_bytes)

## Why it scales significantly better:
   * $O(1)$ Time Complexity: An if/elif chain has $O(N)$ lookup complexity. The 20th message type takes 20 conditions to resolve. A dictionary lookup resolves in $O(1)$ constant time regardless of the number of message types.
   * CPU Branch Prediction: Long conditional chains cause frequent CPU branch mispredictions, flushing the pipeline. Dictionary function pointers reduce branch overhead.
   * Maintainability & Decoupling: Adding a new message type requires adding one key-value pair without modifying core control-flow logic.

## Responsibilities of binary_reader.py vs. event_types.py
1. event_types.py:
   * Defines immutable, typed data contracts for all events.
   * Acts as a lightweight schema passed between modules.
   * Holds zero reading or parsing logic.

2. binary_reader.py:
   *  Handles lower-level file I/O (gzip.open).
   * Unpacks binary bytes using struct.unpack().
   * Manages dispatch tables and stock locate filters.
   * Instantiates objects defined in event_types.py.