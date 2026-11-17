# Review notes

## A10 — RAG synchronization

The application rebuilds/synchronizes the RAG Knowledge Base after checkout and payment changes so product and inventory context stays current. This is appropriate for the current demo scale. As the catalog and traffic grow, optimize by updating only affected product documents, moving synchronization to a background job, and measuring freshness and rebuild latency.
