/**
 * Test Fixtures - Dashboard
 * Mock data for dashboard-related tests
 */

export const mockDashboardStats = {
  totalArticles: '12,485',
  activeSources: '58',
  dailyVisitors: '3,247',
  apiCalls: '89.3K',
}

export const mockMonthlyData = [
  { month: 'Jan', articles: 1243, sources: 45, sentiment: 0.65 },
  { month: 'Feb', articles: 1389, sources: 48, sentiment: 0.58 },
  { month: 'Mar', articles: 1576, sources: 52, sentiment: 0.62 },
  { month: 'Apr', articles: 1832, sources: 51, sentiment: 0.71 },
  { month: 'May', articles: 2103, sources: 55, sentiment: 0.68 },
  { month: 'Jun', articles: 2485, sources: 58, sentiment: 0.73 },
]

export const mockTopicDistribution = [
  { name: 'Politics', value: 35, color: '#f59e0b' },
  { name: 'Economy', value: 28, color: '#10b981' },
  { name: 'Social', value: 20, color: '#3b82f6' },
  { name: 'Technology', value: 10, color: '#8b5cf6' },
  { name: 'Culture', value: 7, color: '#ec4899' },
]

export const mockSentimentTrend = [
  { date: 'Mon', positive: 320, negative: 180, neutral: 200 },
  { date: 'Tue', positive: 380, negative: 160, neutral: 220 },
  { date: 'Wed', positive: 350, negative: 200, neutral: 180 },
  { date: 'Thu', positive: 420, negative: 140, neutral: 240 },
  { date: 'Fri', positive: 480, negative: 120, neutral: 260 },
  { date: 'Sat', positive: 390, negative: 150, neutral: 210 },
  { date: 'Sun', positive: 340, negative: 170, neutral: 190 },
]
