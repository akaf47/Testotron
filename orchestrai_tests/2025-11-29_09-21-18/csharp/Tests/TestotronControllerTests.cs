```csharp
using Xunit;
using Moq;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using System;
using System.Threading.Tasks;
using System.Collections.Generic;
using FluentAssertions;

namespace Testotron.Tests
{
    public class TestotronController
    {
        private readonly ILogger<TestotronController> _logger;
        private readonly ITestService _testService;

        public TestotronController(ILogger<TestotronController> logger, ITestService testService)
        {
            _logger = logger;
            _testService = testService;
        }

        public async Task<IActionResult> RunTests()
        {
            try
            {
                var result = await _testService.ExecuteTestsAsync();
                return new OkObjectResult(result);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error running tests");
                return new BadRequestObjectResult("Failed to run tests");
            }
        }

        public IActionResult GetTestReport(int testId)
        {
            if (testId <= 0)
            {
                return new BadRequestObjectResult("Invalid test ID");
            }

            var report = _testService.GetTestReport(testId);
            if (report == null)
            {
                return new NotFoundResult();
            }

            return new OkObjectResult(report);
        }

        public async Task<IActionResult> ConfigureTests([FromBody] TestConfiguration config)
        {
            if (config == null)
            {
                return new BadRequestObjectResult("Configuration cannot be null");
            }

            try
            {
                await _testService.ConfigureAsync(config);
                return new OkResult();
            }
            catch (ArgumentException ex)
            {
                return new BadRequestObjectResult(ex.Message);
            }
        }
    }

    public interface ITestService
    {
        Task<TestResult> ExecuteTestsAsync();
        TestReport GetTestReport(int testId);
        Task ConfigureAsync(TestConfiguration config);
    }

    public class TestResult
    {
        public bool Success { get; set; }
        public int TestsRun { get; set; }
        public int TestsPassed { get; set; }
        public int TestsFailed { get; set; }
        public string Message { get; set; }
    }

    public class TestReport
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public DateTime ExecutionTime { get; set; }
        public List<string> Details { get; set; }
    }

    public class TestConfiguration
    {
        public int Timeout { get; set; }
        public bool Verbose { get; set; }
        public string Environment { get; set; }
    }

    public class TestotronControllerTests
    {
        private readonly Mock<ILogger<TestotronController>> _mockLogger;
        private readonly Mock<ITestService> _mockTestService;
        private readonly TestotronController _controller;

        public TestotronControllerTests()
        {
            _mockLogger = new Mock<ILogger<TestotronController>>();
            _mockTestService = new Mock<ITestService>();
            _controller =