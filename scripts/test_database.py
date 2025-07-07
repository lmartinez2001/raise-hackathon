from transcribe_and_store import TranscriptionChromaDB


database_path = ... # TODO - add path to database
num_results = 1 # TODO - add number of results to return


# Load the database.
transcriber = TranscriptionChromaDB(database_path=database_path)

# Print database stats.
stats = transcriber.get_collection_stats()
print(stats)

# Print all entries in the database.
print(f"Total segments in database: {stats['total_segments']}")
print(f"Unique videos: {stats['unique_videos']}")
print("\nAll segments:")
print("-" * 80)
for video_id in stats['video_ids']:
    segments = transcriber.get_segments_by_video(video_id)
    print(f"\nVideo: {video_id}")
    print("-" * 40)
    for segment in segments:
        metadata = segment['metadata']
        print(f"[{metadata.get('timestamp_range', 'N/A')}] {segment['text']}")


# Query the database.
search_queries = [
    "migrate",
    "docker",
    "LLM"
]

for query in search_queries:
    print(f"\nSearching for: '{query}'")
    search_results = transcriber.search_segments(query, n_results=1)

    if search_results["results"]["documents"]:
        for i, (doc, metadata) in enumerate(zip(
            search_results["results"]["documents"][0],
            search_results["results"]["metadatas"][0]
        )):
            print(f"  Result {i+1}: {doc[:100]}...")
            print(f"    Video: {metadata.get('video_id', 'unknown')}")
            print(f"    Timestamp: {metadata.get('timestamp_range', 'N/A')}")
    else:
        print("  No results found")



