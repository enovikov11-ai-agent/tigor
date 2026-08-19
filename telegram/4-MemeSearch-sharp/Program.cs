// using Microsoft.Extensions.VectorData;
// using Microsoft.SemanticKernel;
// using Microsoft.SemanticKernel.Connectors.Weaviate;
// using Microsoft.SemanticKernel.Embeddings;

static string GetEnv(string name)
{
    return Environment.GetEnvironmentVariable(name)
    ?? throw new InvalidOperationException("MEMESEARCH_API_KEY env not set");
}

var apiKey = GetEnv("MEMESEARCH_API_KEY");
var weaviateEndpoint = Environment.GetEnvironmentVariable("WEAVIATE_ENDPOINT")
    ?? throw new InvalidOperationException("WEAVIATE_ENDPOINT env not set");
var weaviateKey = Environment.GetEnvironmentVariable("WEAVIATE_API_KEY")
    ?? throw new InvalidOperationException("WEAVIATE_API_KEY env not set");


var bot = new MemeBot(apiKey);
Console.WriteLine("Bot is running. Press Ctrl+C to exit.");
await Task.Delay(-1);

// Hi, when registering an implementation of IVectorStore, you should use kernel.Services.GetRequiredService<IVectorStore>() instead of IMemoryStore. IMemoryStore is obsolete and should no longer be used 



// var httpClient = new HttpClient
// {
//     BaseAddress = new Uri(weaviateEndpoint)
// };

// var options = new WeaviateVectorStoreOptions
// {
//     ApiKey = weaviateKey
// };

// var weaviateVectorStore = new WeaviateVectorStore(httpClient, options);

// weaviateVectorStore.Cre


