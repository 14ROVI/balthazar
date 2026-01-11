from db import Database

import numpy as np
from sklearn.cluster import DBSCAN, AgglomerativeClustering
import asyncio
import hdbscan
from sklearn.manifold import SpectralEmbedding

class EventReclusterer:
    def __init__(self, db: Database):
        self.db = db
        
        # 1. TUNING PARAMETERS
        # eps: Max distance between two points to be considered neighbors.
        # 0.25 (Cosine Distance) is usually a good starting point for "Same Event"
        self.DISTANCE_THRESHOLD = 0.08
        self.MIN_SAMPLES = 2  # Need at least 2 posts to form a cluster
        
    def run_recluster_job(self):
               
        print("🔄 Starting Background Re-clustering...")
        
        rows = self.db.get_all_embeddings()
        
        if not rows:
            return

        embeddings = np.array([r.embedding for r in rows])


        reducer = SpectralEmbedding(
            n_components=10,
            affinity="nearest_neighbors",
            n_neighbors=15,
            n_jobs=-1
        )
        reduced_data = reducer.fit_transform(embeddings)

        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=5,
            min_samples=1,
            metric="euclidean",
            cluster_selection_method="eom"
        )
        labels = clusterer.fit_predict(reduced_data)
        
        self._sync_clusters_to_db(rows, labels)
        
        print("✅ Re-clustering complete.")

    def _sync_clusters_to_db(self, posts, labels):
       
        # Group posts by their NEW cluster label
        clusters = {}
        for i, label in enumerate(labels):
            if label == -1: continue # Ignore noise
            if label not in clusters: clusters[label] = []
            clusters[label].append(i) # Store the index

        self.db.clear_events()

        # For each new mathematical cluster...
        for label, indices in clusters.items():
            # Get the post IDs in this cluster
            cluster_posts = [posts[i] for i in indices]
            cluster_embeddings = [post.embedding for post in posts]
            
            # CALCULATE NEW CENTROID (The "Perfect" Center)
            new_centroid = np.mean(cluster_embeddings, axis=0)
            # Normalize it!
            new_centroid = new_centroid / np.linalg.norm(new_centroid)
            
            event = self.db.add_event(cluster_posts[0].content, 10, new_centroid)
            for post in cluster_posts:
                self.db.set_intelligence_event(post.url, event.id)


async def main():
    database = Database()
    reclusterer = EventReclusterer(database)
    reclusterer.run_recluster_job()

if __name__ == "__main__":
    asyncio.run(main())