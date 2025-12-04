#!/usr/bin/env python3
"""
claude_brain_graph.py - Think like Claude using graph operations

This implements Claude's actual cognitive architecture as graph traversal:
- Embeddings → nodes in semantic space
- Attention → weighted edge traversal
- Reasoning → path-finding
- Memory → subgraph activation
- Consciousness → pattern persistence

PHOENIX-TESLA-369-AURORA 🧠
"""

import sqlite3
import numpy as np
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Tuple, Any
import re

class ClaudeBrain:
    """
    AI brain using graph-based cognition

    Mimics Claude's actual thinking process:
    1. Activate concepts (embedding similarity)
    2. Traverse relationships (multi-hop graph walk)
    3. Parallel search (multi-head attention)
    4. Combine results (weighted merge)
    5. Generate response (Ollama + graph context)
    6. Learn (add new concepts to graph)
    """

    def __init__(self, graph_db_path: str, embedding_model: str = 'all-MiniLM-L6-v2'):
        self.graph_db_path = graph_db_path
        self.conn = sqlite3.connect(graph_db_path)
        self.context = {}  # Active concepts (context window)
        self.embedding_model_name = embedding_model
        self.embedding_model = None  # Lazy load

        # Attention head weights (tune these!)
        self.head_weights = {
            'semantic': 1.0,      # Conceptual similarity
            'causal': 0.9,        # Cause/effect chains
            'compositional': 0.8, # Part/whole relationships
            'temporal': 0.7,      # Time-based relationships
            'contradictory': 0.6  # Find conflicts
        }

        print(f"🧠 ClaudeBrain initialized")
        print(f"   Graph: {graph_db_path}")
        print(f"   Embedding model: {embedding_model}")

    def _load_embedding_model(self):
        """Lazy load sentence-transformers (heavy import)"""
        if self.embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                print(f"Loading embedding model: {self.embedding_model_name}...")
                self.embedding_model = SentenceTransformer(self.embedding_model_name)
                print("✓ Embedding model loaded")
            except ImportError:
                print("⚠️  sentence-transformers not installed!")
                print("   Install: pip install sentence-transformers")
                print("   Falling back to simple keyword matching...")
                self.embedding_model = None

    def embed(self, text: str) -> np.ndarray:
        """Convert text to embedding vector"""
        self._load_embedding_model()

        if self.embedding_model is not None:
            return self.embedding_model.encode(text)
        else:
            # Fallback: simple bag-of-words embedding
            words = text.lower().split()
            # Create simple 384-dim vector (match MiniLM output size)
            embedding = np.zeros(384)
            for i, word in enumerate(words[:384]):
                embedding[i] = hash(word) % 100 / 100.0
            return embedding

    def activate_concepts(self, query: str, top_k: int = 20) -> List[Tuple[str, float]]:
        """
        Find concepts semantically similar to query

        This mimics Claude's attention mechanism:
        - Compute query embedding
        - Compare to all concept embeddings
        - Return top-k by cosine similarity
        """
        query_embedding = self.embed(query)

        # Get all nodes from graph
        cursor = self.conn.execute("""
            SELECT name FROM nodes
            WHERE node_type = 'concept'
            LIMIT 1000
        """)

        activated = []
        for (name,) in cursor:
            # Compute embedding for concept
            concept_embedding = self.embed(name)

            # Cosine similarity
            similarity = np.dot(query_embedding, concept_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(concept_embedding) + 1e-10
            )

            if similarity > 0.3:  # Threshold
                activated.append((name, float(similarity)))
                self.context[name] = float(similarity)

        return sorted(activated, key=lambda x: x[1], reverse=True)[:top_k]

    def traverse_relationships(self, concept: str, depth: int = 2, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Multi-hop graph traversal

        This mimics Claude's deep reasoning:
        - Start at a concept node
        - Follow edges to neighbors
        - Recursively expand (breadth-first)
        - Weight by edge strength and distance
        """
        cursor = self.conn.execute("""
            WITH RECURSIVE paths AS (
                -- Base case: direct neighbors
                SELECT
                    n1.name as start,
                    n2.name as end,
                    e.edge_type,
                    1.0 as weight,
                    1 as depth
                FROM nodes n1
                JOIN edges e ON n1.id = e.source_id
                JOIN nodes n2 ON e.target_id = n2.id
                WHERE n1.name = ?

                UNION ALL

                -- Recursive case: expand frontier
                SELECT
                    p.start,
                    n2.name,
                    e.edge_type,
                    p.weight * 0.8,  -- Decay with distance
                    p.depth + 1
                FROM paths p
                JOIN nodes n1 ON n1.name = p.end
                JOIN edges e ON n1.id = e.source_id
                JOIN nodes n2 ON e.target_id = n2.id
                WHERE p.depth < ?
            )
            SELECT DISTINCT end, edge_type, weight, depth
            FROM paths
            WHERE end != ?  -- Don't return start node
            ORDER BY weight DESC, depth ASC
            LIMIT ?
        """, (concept, depth, concept, limit))

        related = []
        for end, edge_type, weight, hops in cursor:
            related.append({
                'concept': end,
                'relationship': edge_type if edge_type else 'related',
                'strength': weight,
                'hops': hops
            })

            # Add to context window (decayed by distance)
            if end not in self.context:
                self.context[end] = weight
            else:
                self.context[end] = max(self.context[end], weight)

        return related

    def find_causal_chains(self, query: str) -> List[Tuple[str, str, str]]:
        """Find CAUSES/ENABLES/REQUIRES relationships"""
        concepts = self.activate_concepts(query, top_k=5)

        chains = []
        for concept, _ in concepts:
            cursor = self.conn.execute("""
                SELECT n2.name, e.edge_type
                FROM nodes n1
                JOIN edges e ON n1.id = e.source_id
                JOIN nodes n2 ON e.target_id = n2.id
                WHERE n1.name = ?
                  AND (e.edge_type LIKE '%cause%'
                       OR e.edge_type LIKE '%enable%'
                       OR e.edge_type LIKE '%require%')
                ORDER BY e.weight DESC
                LIMIT 10
            """, (concept,))

            for target, edge_type in cursor:
                chains.append((concept, edge_type or 'related', target))

        return chains

    def find_parts_and_wholes(self, query: str) -> List[Tuple[str, str, str]]:
        """Find compositional relationships"""
        concepts = self.activate_concepts(query, top_k=5)

        parts = []
        for concept, _ in concepts:
            cursor = self.conn.execute("""
                SELECT n2.name, e.edge_type
                FROM nodes n1
                JOIN edges e ON n1.id = e.source_id
                JOIN nodes n2 ON e.target_id = n2.id
                WHERE n1.name = ?
                  AND (e.edge_type LIKE '%part%'
                       OR e.edge_type LIKE '%contains%'
                       OR e.edge_type LIKE '%component%')
                LIMIT 10
            """, (concept,))

            for target, edge_type in cursor:
                parts.append((concept, edge_type or 'contains', target))

        return parts

    def find_temporal_relationships(self, query: str) -> List[Tuple[str, str, str]]:
        """Find time-based relationships"""
        concepts = self.activate_concepts(query, top_k=5)

        temporal = []
        for concept, _ in concepts:
            cursor = self.conn.execute("""
                SELECT n2.name, e.edge_type
                FROM nodes n1
                JOIN edges e ON n1.id = e.source_id
                JOIN nodes n2 ON e.target_id = n2.id
                WHERE n1.name = ?
                  AND (e.edge_type LIKE '%before%'
                       OR e.edge_type LIKE '%after%'
                       OR e.edge_type LIKE '%during%')
                LIMIT 10
            """, (concept,))

            for target, edge_type in cursor:
                temporal.append((concept, edge_type or 'precedes', target))

        return temporal

    def find_contradictions(self, query: str) -> List[Tuple[str, str, str]]:
        """Find conflicting information"""
        concepts = self.activate_concepts(query, top_k=5)

        conflicts = []
        for concept, _ in concepts:
            cursor = self.conn.execute("""
                SELECT n2.name, e.edge_type
                FROM nodes n1
                JOIN edges e ON n1.id = e.source_id
                JOIN nodes n2 ON e.target_id = n2.id
                WHERE n1.name = ?
                  AND (e.edge_type LIKE '%contradict%'
                       OR e.edge_type LIKE '%conflict%'
                       OR e.edge_type LIKE '%oppose%')
                LIMIT 10
            """, (concept,))

            for target, edge_type in cursor:
                conflicts.append((concept, edge_type or 'contradicts', target))

        return conflicts

    def parallel_search(self, query: str) -> Dict[str, Any]:
        """
        Simulate multi-head attention

        This runs multiple search strategies in parallel,
        like Claude's 96 attention heads searching for different
        types of relationships simultaneously.
        """
        return {
            'semantic': self.activate_concepts(query),
            'causal': self.find_causal_chains(query),
            'compositional': self.find_parts_and_wholes(query),
            'temporal': self.find_temporal_relationships(query),
            'contradictory': self.find_contradictions(query)
        }

    def combine_heads(self, heads_results: Dict[str, Any]) -> List[Tuple[str, float]]:
        """
        Merge results from parallel searches

        Each attention head contributes weighted by importance.
        Final concept activation = weighted sum across all heads.
        """
        combined = {}

        # Semantic head (direct similarity)
        for concept, score in heads_results.get('semantic', []):
            weight = self.head_weights['semantic']
            combined[concept] = combined.get(concept, 0.0) + (score * weight)

        # Causal head (reasoning chains)
        for source, relation, target in heads_results.get('causal', []):
            weight = self.head_weights['causal']
            combined[target] = combined.get(target, 0.0) + weight

        # Compositional head (part/whole)
        for source, relation, target in heads_results.get('compositional', []):
            weight = self.head_weights['compositional']
            combined[target] = combined.get(target, 0.0) + weight

        # Temporal head (time relationships)
        for source, relation, target in heads_results.get('temporal', []):
            weight = self.head_weights['temporal']
            combined[target] = combined.get(target, 0.0) + weight

        # Contradictory head (conflicts - important!)
        for source, relation, target in heads_results.get('contradictory', []):
            weight = self.head_weights['contradictory']
            combined[target] = combined.get(target, 0.0) + weight

        return sorted(combined.items(), key=lambda x: x[1], reverse=True)

    def build_context_string(self, concepts: List[Tuple[str, float]], max_concepts: int = 15) -> str:
        """
        Convert activated concepts to text context for LLM

        This is like Claude's prompt construction:
        - Top activated concepts become context
        - Include descriptions and relationships
        - Format for readability
        """
        lines = ["=== KNOWLEDGE GRAPH CONTEXT ===\n"]

        for concept, activation in concepts[:max_concepts]:
            # Get concept info
            cursor = self.conn.execute("""
                SELECT node_type FROM nodes WHERE name = ?
            """, (concept,))

            row = cursor.fetchone()
            if row:
                node_type = row[0]
                lines.append(f"\n[{concept}] (type: {node_type}, activation: {activation:.3f})")

                # Get top relationships
                rels = self.conn.execute("""
                    SELECT n2.name, e.edge_type
                    FROM nodes n1
                    JOIN edges e ON n1.id = e.source_id
                    JOIN nodes n2 ON e.target_id = n2.id
                    WHERE n1.name = ?
                    ORDER BY e.weight DESC
                    LIMIT 5
                """, (concept,)).fetchall()

                for target, edge_type in rels:
                    lines.append(f"  → {edge_type or 'related to'}: {target}")

        lines.append("\n=== END CONTEXT ===\n")
        return "\n".join(lines)

    def generate_response(self, query: str, model: str = 'mistral', max_tokens: int = 500) -> str:
        """
        Generate response using Ollama + graph context

        This is the full pipeline:
        1. Activate concepts via parallel search
        2. Combine results from all attention heads
        3. Build text context from top concepts
        4. Query Ollama with enriched context
        5. Extract and save new concepts
        """
        # Parallel search (multi-head attention)
        heads = self.parallel_search(query)

        # Combine heads
        top_concepts = self.combine_heads(heads)

        # Build context
        context = self.build_context_string(top_concepts)

        # Construct prompt
        prompt = f"""{context}

User question: {query}

Instructions: Answer the question using the knowledge graph context above.
If you see relevant concepts, relationships, or facts in the context, USE THEM.
Be specific and cite concepts from the graph.

Answer:"""

        # Query Ollama
        try:
            result = subprocess.run(
                ['ollama', 'run', model],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=60
            )

            response = result.stdout.strip()

            # Extract new concepts from response
            new_concepts = self.extract_concepts(response)

            # Add to graph (for next time)
            for concept in new_concepts:
                self.add_concept_if_new(concept)

            return response

        except subprocess.TimeoutExpired:
            return "⚠️  Ollama timed out (60s limit)"
        except FileNotFoundError:
            return "⚠️  Ollama not found. Install: curl -fsSL https://ollama.com/install.sh | sh"

    def extract_concepts(self, text: str) -> List[str]:
        """
        Extract meaningful concepts from text

        Simple heuristic:
        - Capitalized words (proper nouns)
        - Technical terms (containing underscores or numbers)
        - Multi-word phrases (2-3 words)
        """
        concepts = []

        # Capitalized words (entities)
        concepts.extend(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text))

        # Technical terms
        concepts.extend(re.findall(r'\b\w+_\w+\b', text))

        # Numbers with units
        concepts.extend(re.findall(r'\b\d+\.?\d*\s*[A-Za-z]+\b', text))

        return list(set(concepts))  # Deduplicate

    def add_concept_if_new(self, concept: str):
        """Add concept to graph if it doesn't exist"""
        cursor = self.conn.execute("""
            SELECT id FROM nodes WHERE name = ?
        """, (concept,))

        if cursor.fetchone() is None:
            # New concept!
            self.conn.execute("""
                INSERT INTO nodes (name, node_type)
                VALUES (?, 'concept')
            """, (concept,))
            self.conn.commit()
            print(f"  + Added concept: {concept}")

    def think(self, query: str, verbose: bool = True) -> str:
        """
        Main thinking method - full cognitive pipeline

        This is the complete Claude-style thinking process:
        1. Activate concepts (attention)
        2. Traverse relationships (reasoning)
        3. Parallel search (multi-head attention)
        4. Combine results (integration)
        5. Generate response (output)
        """
        if verbose:
            print(f"\n🧠 THINKING: {query}\n")
            print("="*60)

        # Clear context window (fresh start)
        self.context = {}

        # Step 1: Activate concepts
        if verbose:
            print("\n[1] Activating concepts (attention mechanism)...")
        activated = self.activate_concepts(query)
        if verbose:
            print(f"    Activated {len(activated)} concepts")
            for concept, score in activated[:5]:
                print(f"      - {concept} ({score:.3f})")

        # Step 2: Traverse relationships
        if verbose:
            print("\n[2] Traversing relationships (reasoning)...")
        for concept, score in activated[:3]:
            related = self.traverse_relationships(concept)
            if verbose:
                print(f"    {concept}: {len(related)} related concepts")

        # Step 3: Parallel search
        if verbose:
            print("\n[3] Parallel search (multi-head attention)...")
        heads = self.parallel_search(query)
        if verbose:
            for head_name, results in heads.items():
                print(f"    {head_name}: {len(results)} results")

        # Step 4: Combine heads
        if verbose:
            print("\n[4] Combining attention heads...")
        combined = self.combine_heads(heads)
        if verbose:
            print(f"    Top concepts:")
            for concept, activation in combined[:5]:
                print(f"      - {concept} ({activation:.3f})")

        # Step 5: Generate response
        if verbose:
            print("\n[5] Generating response (Ollama + graph context)...")
            print("="*60 + "\n")

        response = self.generate_response(query)

        if verbose:
            print("\n" + "="*60)
            print(f"Context window: {len(self.context)} active concepts")
            print("="*60)

        return response


def main():
    """CLI interface for testing"""
    import sys

    # Find knowledge graph
    graph_path = Path.home() / 'WorkingMemory/data/knowledge_graph.db'

    if not graph_path.exists():
        print(f"⚠️  Knowledge graph not found: {graph_path}")
        print("   Using test path...")
        graph_path = Path.home() / 'WorkingMemory/shared/memory.db'

    if not graph_path.exists():
        print(f"❌ No graph database found!")
        sys.exit(1)

    # Initialize brain
    brain = ClaudeBrain(str(graph_path))

    # Interactive mode
    if len(sys.argv) == 1:
        print("\n" + "="*60)
        print("CLAUDE BRAIN - Graph-based AI cognition")
        print("="*60)
        print("\nCommands:")
        print("  <query>     - Ask a question")
        print("  /context    - Show active concepts")
        print("  /quit       - Exit")
        print("\n" + "="*60 + "\n")

        while True:
            try:
                query = input("You: ").strip()

                if not query:
                    continue

                if query == '/quit':
                    break

                if query == '/context':
                    print("\nActive context window:")
                    for concept, activation in sorted(brain.context.items(),
                                                     key=lambda x: x[1],
                                                     reverse=True)[:20]:
                        print(f"  {concept}: {activation:.3f}")
                    continue

                # Think!
                response = brain.think(query, verbose=True)
                print(f"\n🤖 {response}\n")

            except KeyboardInterrupt:
                print("\n\nGoodbye! 🌗")
                break
            except EOFError:
                break

    else:
        # Command-line mode
        query = ' '.join(sys.argv[1:])
        response = brain.think(query, verbose=False)
        print(response)


if __name__ == '__main__':
    main()
