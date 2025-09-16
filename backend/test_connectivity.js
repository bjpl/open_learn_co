// Simple JavaScript test to verify backend connectivity from frontend
// This can be run in browser console or used in frontend code

async function testBackendConnectivity() {
    const baseUrl = 'http://localhost:8000';

    try {
        console.log('Testing OpenLearn Colombia Backend API...');

        // Test 1: Root endpoint
        const rootResponse = await fetch(`${baseUrl}/`);
        const rootData = await rootResponse.json();
        console.log('✅ Root endpoint:', rootData);

        // Test 2: Health check
        const healthResponse = await fetch(`${baseUrl}/health`);
        const healthData = await healthResponse.json();
        console.log('✅ Health check:', healthData);

        // Test 3: API test endpoint
        const testResponse = await fetch(`${baseUrl}/api/test`);
        const testData = await testResponse.json();
        console.log('✅ API test endpoint:', testData);

        // Test 4: API status
        const statusResponse = await fetch(`${baseUrl}/api/status`);
        const statusData = await statusResponse.json();
        console.log('✅ API status:', statusData);

        console.log('🎉 All tests passed! Backend is ready for frontend integration.');

        return {
            success: true,
            backend_url: baseUrl,
            endpoints_tested: 4,
            cors_enabled: true
        };

    } catch (error) {
        console.error('❌ Backend connectivity test failed:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

// Export for use in frontend
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { testBackendConnectivity };
}

// Auto-run in browser environment
if (typeof window !== 'undefined') {
    testBackendConnectivity();
}