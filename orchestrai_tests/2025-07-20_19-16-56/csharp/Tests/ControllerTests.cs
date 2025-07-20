```csharp
using Xunit;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.AspNetCore.Hosting;
using System.Net.Http;
using System.Threading.Tasks;
using System.Text;
using Newtonsoft.Json;

namespace Testotron.Tests
{
    public class ControllerTests : IClassFixture<WebApplicationFactory<Program>>
    {
        private readonly WebApplicationFactory<Program> _factory;
        private readonly HttpClient _client;

        public ControllerTests(WebApplicationFactory<Program> factory)
        {
            _factory = factory;
            _client = _factory.CreateClient();
        }

        [Fact]
        public async Task Get_Endpoint_Should_Return_Success()
        {
            // Act
            var response = await _client.GetAsync("/api/test");

            // Assert
            response.EnsureSuccessStatusCode();
        }

        [Fact]
        public async Task Post_Endpoint_Should_Accept_Data()
        {
            // Arrange
            var content = new StringContent(
                JsonConvert.SerializeObject(new { test = "data" }),
                Encoding.UTF8,
                "application/json");

            // Act
            var response = await _client.PostAsync("/api/test", content);

            // Assert
            response.EnsureSuccessStatusCode();
        }
    }
}
```