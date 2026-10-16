"""
Generates high-resolution architectural and process flow diagrams
for the Enterprise Knowledge Navigator documentation matching the Teal & Forest palette.
"""

import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Ensure output directory exists
DIAGRAM_DIR = Path("docs/diagrams")
DIAGRAM_DIR.mkdir(parents=True, exist_ok=True)

# Styling Constants - Teal & Forest Theme
FONT_FAMILY = "sans-serif"
COLOR_PRIMARY = "#0F766E"    # Deep Teal
COLOR_SECONDARY = "#115E59"  # Dark Forest Teal
COLOR_SAGE = "#A7C4B5"       # Soft Sage
COLOR_BG_CARD = "#F7FAF8"    # Warm Off-White
COLOR_BORDER = "#DCE8E3"     # Subtle Sage Border
COLOR_TEXT = "#172B2A"       # Deep Charcoal
COLOR_MUTED = "#647875"      # Slate Forest
COLOR_ACCENT = "#0D9488"     # Teal Accent
COLOR_BRASS = "#B7791F"      # Warm Amber / Brass
COLOR_EMERALD = "#16835D"    # Forest Emerald

plt.rcParams["font.family"] = FONT_FAMILY
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]


def create_diagram_overall_architecture():
    """Diagram 1: Overall System Architecture"""
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.5)
    ax.axis("off")

    ax.text(5, 6.1, "Enterprise Knowledge Navigator — Overall System Architecture",
            ha="center", va="center", fontsize=14, weight="bold", color=COLOR_TEXT)

    layers = [
        ("Presentation Layer (Vanilla Single-Page Application)\nHTML5 • Modern Light CSS3 (Teal/Sage) • Pure ES6 JavaScript\nResponsive Dashboard • D3.js v7 Knowledge Graph • Accessible UI", 0.6, 4.8, 8.8, 0.9, "#E4F3EE", "#0F766E"),
        ("API Gateway & Application Controllers (FastAPI)\nREST Endpoints • CORS Middleware • OAuth2 Password Bearer / JWT Security Guard\nRequest Validation (Pydantic v2) • Audit Logging Interceptor • Role Enforcement", 0.6, 3.4, 8.8, 0.9, "#F0FDF4", "#16835D"),
        ("Core AI / ML & Retrieval Engines\nScikit-Learn TF-IDF Vectorizer • Cosine Similarity Matrix • KMeans Cluster Engine\nHybrid Reciprocal Rank Fusion (RRF k=60) • Grounded RAG Synthesis • GraphRAG Expansion", 0.6, 2.0, 8.8, 0.9, "#FEF3C7", "#B7791F"),
        ("Persistence & Storage Repositories\nSQLite 3 (SQLAlchemy 2.0 ORM) • Pickle Vector Index & Metadata JSON Store\nKnowledge Graph Triples (Entities & Relations) • Raw File System (PDF, DOCX, TXT)", 0.6, 0.6, 8.8, 0.9, "#F1F5F9", "#475569"),
    ]

    for title, x, y, w, h, bg, border in layers:
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2",
                                      fc=bg, ec=border, lw=1.8)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, title, ha="center", va="center",
                fontsize=9.5, weight="medium", color=COLOR_TEXT, multialignment="center")

    arrow_y = [4.8, 3.4, 2.0]
    for y in arrow_y:
        ax.annotate("", xy=(5, y), xytext=(5, y + 0.5),
                    arrowprops=dict(arrowstyle="<->", lw=2, color=COLOR_PRIMARY))

    out_file = DIAGRAM_DIR / "arch_overall.png"
    plt.tight_layout()
    plt.savefig(out_file, bbox_inches="tight")
    plt.close()
    print(f"Generated: {out_file}")


def create_diagram_interaction():
    """Diagram 2: Frontend, Backend, and Database Interaction"""
    fig, ax = plt.subplots(figsize=(10, 6.2), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.2)
    ax.axis("off")

    ax.text(5, 5.8, "Client-Server-Database Interaction Flow",
            ha="center", va="center", fontsize=14, weight="bold", color=COLOR_TEXT)

    boxes = [
        ("Client Browser (SPA)\nUser Actions & Navigation\nDOM State Management\nJWT Authorization Headers", 0.5, 2.0, 2.5, 2.5, "#E4F3EE", "#0F766E"),
        ("FastAPI Backend Server\nAuth Controller (/api/v1/auth)\nNavigator API (/api/v1/navigator)\nWorkspace Router (/api/v1/workspace)\nML Analytics (/api/v1/ml)", 3.75, 1.6, 2.5, 3.3, "#F0FDF4", "#16835D"),
        ("Data & File Storage\nknowledge_navigator.db (SQLite)\nDocument Catalog & Chunks\nVectors & Graph Adjacency\nAudit Logs & Password OTPs", 7.0, 2.0, 2.5, 2.5, "#FEF3C7", "#B7791F"),
    ]

    for text, x, y, w, h, bg, border in boxes:
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2",
                                      fc=bg, ec=border, lw=2)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=9.5, weight="medium", color=COLOR_TEXT, multialignment="center")

    ax.annotate("HTTP POST / GET\nBearer Token", xy=(3.75, 3.6), xytext=(3.0, 3.6),
                arrowprops=dict(arrowstyle="->", lw=1.8, color="#0F766E"),
                ha="center", va="bottom", fontsize=8, weight="bold")
    ax.annotate("JSON Responses\nPaginated Data", xy=(3.0, 2.8), xytext=(3.75, 2.8),
                arrowprops=dict(arrowstyle="->", lw=1.8, color="#16835D"),
                ha="center", va="top", fontsize=8, weight="bold")

    ax.annotate("SQLAlchemy Queries\nFile I/O", xy=(7.0, 3.6), xytext=(6.25, 3.6),
                arrowprops=dict(arrowstyle="->", lw=1.8, color="#16835D"),
                ha="center", va="bottom", fontsize=8, weight="bold")
    ax.annotate("ResultSets & Chunks\nRecord Persistence", xy=(6.25, 2.8), xytext=(7.0, 2.8),
                arrowprops=dict(arrowstyle="->", lw=1.8, color="#B7791F"),
                ha="center", va="top", fontsize=8, weight="bold")

    out_file = DIAGRAM_DIR / "arch_interaction.png"
    plt.tight_layout()
    plt.savefig(out_file, bbox_inches="tight")
    plt.close()
    print(f"Generated: {out_file}")


def create_diagram_ingestion():
    """Diagram 3: Document Ingestion and Indexing Pipeline"""
    fig, ax = plt.subplots(figsize=(10, 5.8), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.8)
    ax.axis("off")

    ax.text(5, 5.3, "Multi-Format Ingestion & Dual Indexing Pipeline",
            ha="center", va="center", fontsize=14, weight="bold", color=COLOR_TEXT)

    steps = [
        ("1. File Upload\nPDF, DOCX, TXT\n(Size <= 25MB)", 0.4, 2.2, 1.5, 1.8, "#E4F3EE", "#0F766E"),
        ("2. Validation &\nDeduplication\nSHA-256 Hash Check", 2.3, 2.2, 1.5, 1.8, "#F0FDF4", "#16835D"),
        ("3. Multi-Format\nExtraction\nPyPDF2, python-docx", 4.2, 2.2, 1.5, 1.8, "#FEF3C7", "#B7791F"),
        ("4. Overlapping\nChunking\nTokens + Page Offset", 6.1, 2.2, 1.5, 1.8, "#ECFDF5", "#0D9488"),
        ("5. Dual Indexing\nVector Store +\nKnowledge Graph", 8.0, 2.2, 1.6, 1.8, "#E6FFFA", "#115E59"),
    ]

    for text, x, y, w, h, bg, border in steps:
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                                      fc=bg, ec=border, lw=1.8)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=8.5, weight="medium", color=COLOR_TEXT, multialignment="center")

    for i in range(len(steps) - 1):
        x1 = steps[i][1] + steps[i][3]
        x2 = steps[i+1][1]
        ax.annotate("", xy=(x2, 3.1), xytext=(x1, 3.1),
                    arrowprops=dict(arrowstyle="->", lw=2, color=COLOR_PRIMARY))

    ax.text(8.8, 1.4, "➔ TF-IDF Inverted Index (Pickle / JSON)\n➔ Entity & Relation Triples (SQLite & JSON)",
            ha="center", va="top", fontsize=8.5, weight="bold", color=COLOR_PRIMARY)

    out_file = DIAGRAM_DIR / "pipeline_ingest.png"
    plt.tight_layout()
    plt.savefig(out_file, bbox_inches="tight")
    plt.close()
    print(f"Generated: {out_file}")


def create_diagram_hybrid_search():
    """Diagram 4: Hybrid Search and Grounded RAG Question-Answering Flow"""
    fig, ax = plt.subplots(figsize=(10, 6.0), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.0)
    ax.axis("off")

    ax.text(5, 5.5, "Hybrid Retrieval & Grounded RAG Generation Flow",
            ha="center", va="center", fontsize=14, weight="bold", color=COLOR_TEXT)

    rect_q = patches.FancyBboxPatch((0.5, 2.4), 1.8, 1.4, boxstyle="round,pad=0.15",
                                    fc="#E4F3EE", ec="#0F766E", lw=2)
    ax.add_patch(rect_q)
    ax.text(1.4, 3.1, "User Query\nNatural Language\nor Search Term", ha="center", va="center",
            fontsize=9, weight="bold", color=COLOR_TEXT)

    rect_b1 = patches.FancyBboxPatch((3.0, 3.5), 1.8, 1.3, boxstyle="round,pad=0.15",
                                     fc="#F0FDF4", ec="#16835D", lw=1.8)
    ax.add_patch(rect_b1)
    ax.text(3.9, 4.15, "Dense Semantic\nVector Search\nCosine Similarity", ha="center", va="center",
            fontsize=8.5, weight="medium", color=COLOR_TEXT)

    rect_b2 = patches.FancyBboxPatch((3.0, 1.5), 1.8, 1.3, boxstyle="round,pad=0.15",
                                     fc="#FEF3C7", ec="#B7791F", lw=1.8)
    ax.add_patch(rect_b2)
    ax.text(3.9, 2.15, "Lexical Keyword\nSearch\nTerm Frequency", ha="center", va="center",
            fontsize=8.5, weight="medium", color=COLOR_TEXT)

    rect_rrf = patches.FancyBboxPatch((5.4, 2.3), 1.8, 1.6, boxstyle="round,pad=0.15",
                                      fc="#ECFDF5", ec="#0D9488", lw=2)
    ax.add_patch(rect_rrf)
    ax.text(6.3, 3.1, "Reciprocal Rank\nFusion (RRF k=60)\nRank Harmonization\nTop-K Selection",
            ha="center", va="center", fontsize=8.5, weight="bold", color=COLOR_TEXT)

    rect_rag = patches.FancyBboxPatch((7.8, 2.1), 1.9, 2.0, boxstyle="round,pad=0.15",
                                      fc="#E6FFFA", ec="#115E59", lw=2)
    ax.add_patch(rect_rag)
    ax.text(8.75, 3.1, "Grounded RAG\nSynthesis\nContext Ingestion\nLLM Generation\nPage Citations [p.X]",
            ha="center", va="center", fontsize=8.5, weight="bold", color=COLOR_TEXT)

    ax.annotate("", xy=(3.0, 4.15), xytext=(2.3, 3.5), arrowprops=dict(arrowstyle="->", lw=1.8, color=COLOR_PRIMARY))
    ax.annotate("", xy=(3.0, 2.15), xytext=(2.3, 2.7), arrowprops=dict(arrowstyle="->", lw=1.8, color=COLOR_PRIMARY))
    ax.annotate("", xy=(5.4, 3.4), xytext=(4.8, 3.9), arrowprops=dict(arrowstyle="->", lw=1.8, color=COLOR_PRIMARY))
    ax.annotate("", xy=(5.4, 2.8), xytext=(4.8, 2.3), arrowprops=dict(arrowstyle="->", lw=1.8, color=COLOR_PRIMARY))
    ax.annotate("", xy=(7.8, 3.1), xytext=(7.2, 3.1), arrowprops=dict(arrowstyle="->", lw=2, color=COLOR_PRIMARY))

    out_file = DIAGRAM_DIR / "flow_search_rag.png"
    plt.tight_layout()
    plt.savefig(out_file, bbox_inches="tight")
    plt.close()
    print(f"Generated: {out_file}")


def create_diagram_knowledge_graph():
    """Diagram 5: Knowledge Graph Pipeline & GraphRAG Traversal"""
    fig, ax = plt.subplots(figsize=(10, 5.8), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.8)
    ax.axis("off")

    ax.text(5, 5.3, "Knowledge Graph Construction & GraphRAG Subgraph Traversal",
            ha="center", va="center", fontsize=14, weight="bold", color=COLOR_TEXT)

    steps = [
        ("Document Text\nSegmented Chunks\nwith Page Offsets", 0.5, 2.0, 1.8, 1.8, "#E4F3EE", "#0F766E"),
        ("Entity & Relation\nExtraction\nRegex & Entity Rules\n5 Canonical Types", 2.8, 2.0, 1.8, 1.8, "#F0FDF4", "#16835D"),
        ("Graph Storage\nSQLite Triples &\nJSON Adjacency\nEntities & Edges", 5.1, 2.0, 1.8, 1.8, "#FEF3C7", "#B7791F"),
        ("GraphRAG Traversal\nMulti-Hop Paths\nConnected Evidence\nContext Expansion", 7.4, 2.0, 2.1, 1.8, "#E6FFFA", "#115E59"),
    ]

    for text, x, y, w, h, bg, border in steps:
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                                      fc=bg, ec=border, lw=1.8)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=8.5, weight="medium", color=COLOR_TEXT, multialignment="center")

    for i in range(len(steps) - 1):
        x1 = steps[i][1] + steps[i][3]
        x2 = steps[i+1][1]
        ax.annotate("", xy=(x2, 2.9), xytext=(x1, 2.9),
                    arrowprops=dict(arrowstyle="->", lw=2, color=COLOR_PRIMARY))

    out_file = DIAGRAM_DIR / "pipeline_graph.png"
    plt.tight_layout()
    plt.savefig(out_file, bbox_inches="tight")
    plt.close()
    print(f"Generated: {out_file}")


def create_diagram_user_journey():
    """Diagram 6: End-to-End User Journey"""
    fig, ax = plt.subplots(figsize=(10, 6.2), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.2)
    ax.axis("off")

    ax.text(5, 5.7, "Complete End-to-End User Journey Workflow",
            ha="center", va="center", fontsize=14, weight="bold", color=COLOR_TEXT)

    nodes = [
        ("Step 1: Public Visit\nExplore Landing Page\nReview Value Props\nSelect Login / Sign Up", 0.5, 3.2, 2.7, 1.6, "#E4F3EE", "#0F766E"),
        ("Step 2: Authenticate\nRole-Based Login\nor Verified Registration\n(Password Policy + OTP)", 3.65, 3.2, 2.7, 1.6, "#F0FDF4", "#16835D"),
        ("Step 3: Document Ingest\nUpload PDF, DOCX, TXT\nSHA-256 Deduplication\nChunking & Dual Indexing", 6.8, 3.2, 2.7, 1.6, "#FEF3C7", "#B7791F"),
        ("Step 6: Graph & Admin\nExplore Connected Topology\nInspect Quality Benchmarks\nReview Tamper Audit Logs", 6.8, 0.8, 2.7, 1.6, "#E6FFFA", "#115E59"),
        ("Step 5: Verify Citations\nClick Citation Badges\nPaginated Modal Preview\nBookmark & Add Notes", 3.65, 0.8, 2.7, 1.6, "#ECFDF5", "#0D9488"),
        ("Step 4: Search & Ask AI\nExecute Hybrid Retrieval\nDense Vector + Keyword\nGrounded RAG Synthesis", 0.5, 0.8, 2.7, 1.6, "#FAF5FF", "#7C3AED"),
    ]

    for text, x, y, w, h, bg, border in nodes:
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                                      fc=bg, ec=border, lw=1.8)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=8.5, weight="medium", color=COLOR_TEXT, multialignment="center")

    ax.annotate("", xy=(3.65, 4.0), xytext=(3.2, 4.0), arrowprops=dict(arrowstyle="->", lw=2, color=COLOR_PRIMARY))
    ax.annotate("", xy=(6.8, 4.0), xytext=(6.35, 4.0), arrowprops=dict(arrowstyle="->", lw=2, color=COLOR_PRIMARY))
    ax.annotate("", xy=(8.15, 2.4), xytext=(8.15, 3.2), arrowprops=dict(arrowstyle="->", lw=2, color=COLOR_PRIMARY))
    ax.annotate("", xy=(6.35, 1.6), xytext=(6.8, 1.6), arrowprops=dict(arrowstyle="<-", lw=2, color=COLOR_PRIMARY))
    ax.annotate("", xy=(3.2, 1.6), xytext=(3.65, 1.6), arrowprops=dict(arrowstyle="<-", lw=2, color=COLOR_PRIMARY))

    out_file = DIAGRAM_DIR / "user_journey.png"
    plt.tight_layout()
    plt.savefig(out_file, bbox_inches="tight")
    plt.close()
    print(f"Generated: {out_file}")


def generate_all_diagrams():
    print("Generating architectural and process flow diagrams with Teal & Forest theme...")
    create_diagram_overall_architecture()
    create_diagram_interaction()
    create_diagram_ingestion()
    create_diagram_hybrid_search()
    create_diagram_knowledge_graph()
    create_diagram_user_journey()
    print("All 6 diagrams regenerated successfully!")


if __name__ == "__main__":
    generate_all_diagrams()
