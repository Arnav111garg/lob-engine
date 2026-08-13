from __future__ import annotations

import sys
from pathlib import Path

# Add repo root to path so imports work when running `streamlit run`
_REPO_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from lob_analytics.parser import LOBSTERParser
from lob_analytics.engine.reconstruction import ReconstructionEngine
from lob_analytics.analytics.metrics import compute_metrics
from lob_analytics.analytics.queueing import fill_probability


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def plot_ladder(book, highlight_price: int | None = None, num_levels: int = 10):
    """
    Plotly horizontal bar chart of the order book ladder.
    Bids extend left (negative), asks extend right (positive).
    """
    snap = book.snapshot_level2(top_n=num_levels)
    bid_prices = [p for p, _ in snap["bids"]]
    bid_sizes = [s for _, s in snap["bids"]]
    ask_prices = [p for p, _ in snap["asks"]]
    ask_sizes = [s for _, s in snap["asks"]]

    fig = go.Figure()

    # Bids: negative sizes so bars extend left
    fig.add_trace(
        go.Bar(
            y=bid_prices,
            x=[-s for s in bid_sizes],
            orientation="h",
            name="Bids",
            marker_color="rgba(0, 128, 0, 0.7)",
            hovertemplate="Price: %{y}<br>Size: %{customdata}<extra>Bid</extra>",
            customdata=bid_sizes,
        )
    )

    # Asks
    fig.add_trace(
        go.Bar(
            y=ask_prices,
            x=ask_sizes,
            orientation="h",
            name="Asks",
            marker_color="rgba(255, 0, 0, 0.7)",
            hovertemplate="Price: %{y}<br>Size: %{customdata}<extra>Ask</extra>",
            customdata=ask_sizes,
        )
    )

    if highlight_price is not None:
        fig.add_hline(y=highlight_price, line_dash="dot", line_color="yellow")

    fig.update_layout(
        barmode="relative",
        xaxis_title="Depth",
        yaxis_title="Price",
        title="Order Book Ladder",
        height=500,
        template="plotly_white",
    )
    return fig


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #
st.set_page_config(page_title="LOB Analytics", layout="wide")
st.sidebar.title("LOB Analytics")
mode = st.sidebar.radio(
    "Select Mode",
    ["Data Overview", "Reconstruction & Validation", "Event Inspector"],
)

st.title("Limit Order Book Analytics")

# --------------------------------------------------------------------------- #
# Mode 1: Data Overview
# --------------------------------------------------------------------------- #
if mode == "Data Overview":
    st.header("1. Upload LOBSTER Data")
    msg_file = st.file_uploader("Message CSV", type="csv")
    ob_file = st.file_uploader("Orderbook CSV (optional)", type="csv")

    if msg_file is not None:
        df_msg = pd.read_csv(
            msg_file,
            header=None,
            names=["time", "event_type", "order_id", "size", "price", "direction"],
        )

        st.subheader("Message Statistics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Messages", f"{len(df_msg):,}")
        col2.metric("Time Range (s)", f"{df_msg['time'].max() - df_msg['time'].min():.2f}")
        col3.metric("Tick Size (raw)", int(df_msg[df_msg["price"] > 0]["price"].diff().abs().min()))

        st.subheader("Event Type Distribution")
        event_counts = df_msg["event_type"].value_counts().sort_index()
        event_names = {1: "ADD", 2: "CANCEL", 3: "DELETE", 4: "EXECUTE", 5: "HIDDEN"}
        event_counts.index = event_counts.index.map(lambda x: event_names.get(x, f"TYPE_{x}"))
        st.bar_chart(event_counts)

        st.subheader("Spread Over First 10,000 Events")
        if ob_file is not None:
            df_ob = pd.read_csv(ob_file, header=None)
            # Assume ask_price_1 = col 0, bid_price_1 = col 20
            ask1 = df_ob.iloc[:10000, 0]
            bid1 = df_ob.iloc[:10000, 20]
            spread = ask1 - bid1
            spread_df = pd.DataFrame({"Spread": spread.values})
            st.line_chart(spread_df)
        else:
            st.info("Upload the orderbook CSV to see the spread chart.")

# --------------------------------------------------------------------------- #
# Mode 2: Reconstruction & Validation
# --------------------------------------------------------------------------- #
elif mode == "Reconstruction & Validation":
    st.header("2. Reconstruct from Message Stream")
    msg_file = st.file_uploader("Message CSV", type="csv")

    if msg_file is not None:
        if st.button("Run Full Reconstruction"):
            with st.spinner("Reconstructing..."):
                # Save uploaded file to temp path
                tmp_path = Path("/tmp/lob_msg.csv")
                tmp_path.write_bytes(msg_file.getvalue())

                parser = LOBSTERParser()
                events = parser.parse_events(tmp_path)
                engine = ReconstructionEngine(validate_conservation=True)

                progress_bar = st.progress(0)
                status_text = st.empty()

                count = 0
                try:
                    for event in events:
                        engine.process_event(event)
                        count += 1
                        if count % 50_000 == 0:
                            progress = min(count / 624_040, 1.0)
                            progress_bar.progress(progress)
                            status_text.text(f"Processed {count:,} events...")
                except RuntimeError as exc:
                    st.error(f"Reconstruction halted at event {count}: {exc}")
                    st.stop()

                progress_bar.progress(1.0)
                status_text.text(f"Done. Processed {count:,} events.")

            st.success("Reconstruction complete. Book is healthy.")

            snap = engine.book.snapshot_level2(top_n=5)
            st.subheader("Final Book Snapshot (Top 5 Levels)")
            col_bid, col_ask = st.columns(2)
            with col_bid:
                st.write("**Bids**")
                st.write(snap["bids"])
            with col_ask:
                st.write("**Asks**")
                st.write(snap["asks"])

            metrics = compute_metrics(engine.book)
            st.subheader("Final Metrics")
            st.json({
                "Best Bid": metrics.best_bid,
                "Best Ask": metrics.best_ask,
                "Spread": metrics.spread,
                "Mid": metrics.mid_price,
                "Weighted Mid": metrics.weighted_mid,
                "Depth Imbalance": metrics.depth_imbalance,
            })

# --------------------------------------------------------------------------- #
# Mode 3: Event Inspector
# --------------------------------------------------------------------------- #
elif mode == "Event Inspector":
    st.header("3. Inspect Event-by-Event")
    msg_file = st.file_uploader("Message CSV", type="csv")

    if msg_file is not None:
        tmp_path = Path("/tmp/lob_msg_inspect.csv")
        tmp_path.write_bytes(msg_file.getvalue())

        # Load messages into DataFrame for fast indexing
        df = pd.read_csv(
            tmp_path,
            header=None,
            names=["time", "event_type", "order_id", "size", "price", "direction"],
        )
        n_events = len(df)

        event_idx = st.slider("Event Index", 0, n_events - 1, 0)

        # Show message details
        row = df.iloc[event_idx]
        event_names = {1: "ADD", 2: "CANCEL", 3: "DELETE", 4: "EXECUTE", 5: "HIDDEN"}
        side_names = {-1: "SELL", 1: "BUY"}

        st.subheader(f"Message #{event_idx}")
        st.json({
            "Time (s since midnight)": float(row["time"]),
            "Event Type": event_names.get(int(row["event_type"]), f"TYPE_{int(row['event_type'])}"),
            "Order ID": int(row["order_id"]),
            "Size": int(row["size"]),
            "Price": int(row["price"]),
            "Direction": side_names.get(int(row["direction"]), "UNKNOWN"),
        })

        # Reconstruct up to this event
        with st.spinner("Reconstructing book state..."):
            parser = LOBSTERParser()
            events = parser.parse_events(tmp_path)
            engine = ReconstructionEngine(validate_conservation=False)

            for i, event in enumerate(events):
                if i > event_idx:
                    break
                engine.process_event(event)

        st.subheader(f"Book State After Message #{event_idx}")
        metrics = compute_metrics(engine.book)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Best Bid", metrics.best_bid or "-")
        c2.metric("Best Ask", metrics.best_ask or "-")
        c3.metric("Spread", metrics.spread or "-")
        c4.metric("Mid", f"{metrics.mid_price:.4f}" if metrics.mid_price else "-")

        # Ladder plot
        st.plotly_chart(plot_ladder(engine.book), use_container_width=True)

        # Queue position & fill probability at touch
        if metrics.best_bid and metrics.best_ask:
            st.subheader("Queue Position Analysis (Best Bid)")
            level = engine.book.bids.get(metrics.best_bid)
            if level and len(level) > 0:
                mu = st.number_input("Execution rate μ", value=2.0, min_value=0.01)
                theta = st.number_input("Cancel rate θ", value=1.0, min_value=0.01)

                qp_data = []
                for k, order in enumerate(level, start=1):
                    fp = fill_probability(k, mu, theta)
                    qp_data.append({
                        "Position k": k,
                        "Order ID": order.order_id,
                        "Size": order.quantity,
                        "Fill Prob f_k": f"{fp:.4f}",
                    })
                st.table(qd.DataFrame(qp_data))