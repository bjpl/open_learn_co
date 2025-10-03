'use client'

import { Activity, TrendingUp, Users, FileText, Database } from 'lucide-react'
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import StatsCard from '@/components/StatsCard'
import SourceStatus from '@/components/SourceStatus'
import { RouteErrorBoundary, ComponentErrorBoundary } from '@/components/error-boundary'

const monthlyData = [
  { month: 'Jan', articles: 1243, sources: 45, sentiment: 0.65 },
  { month: 'Feb', articles: 1389, sources: 48, sentiment: 0.58 },
  { month: 'Mar', articles: 1576, sources: 52, sentiment: 0.62 },
  { month: 'Apr', articles: 1832, sources: 51, sentiment: 0.71 },
  { month: 'May', articles: 2103, sources: 55, sentiment: 0.68 },
  { month: 'Jun', articles: 2485, sources: 58, sentiment: 0.73 },
]

const topicDistribution = [
  { name: 'Politics', value: 35, color: '#f59e0b' },
  { name: 'Economy', value: 28, color: '#10b981' },
  { name: 'Social', value: 20, color: '#3b82f6' },
  { name: 'Technology', value: 10, color: '#8b5cf6' },
  { name: 'Culture', value: 7, color: '#ec4899' },
]

const sentimentTrend = [
  { date: 'Mon', positive: 320, negative: 180, neutral: 200 },
  { date: 'Tue', positive: 380, negative: 160, neutral: 220 },
  { date: 'Wed', positive: 350, negative: 200, neutral: 180 },
  { date: 'Thu', positive: 420, negative: 140, neutral: 240 },
  { date: 'Fri', positive: 480, negative: 120, neutral: 260 },
  { date: 'Sat', positive: 390, negative: 150, neutral: 210 },
  { date: 'Sun', positive: 340, negative: 170, neutral: 190 },
]

export default function Dashboard() {
  return (
    <RouteErrorBoundary>
      <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-yellow-500 to-orange-600 rounded-lg p-8 text-white">
        <h1 className="text-4xl font-bold mb-2">Colombian Data Intelligence Dashboard</h1>
        <p className="text-yellow-100 text-lg">
          Real-time insights from {monthlyData[monthlyData.length - 1].sources} active sources
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total Articles"
          value="12,485"
          change={12.5}
          icon={FileText}
          trend="up"
        />
        <StatsCard
          title="Active Sources"
          value="58"
          change={7.8}
          icon={Database}
          trend="up"
        />
        <StatsCard
          title="Daily Visitors"
          value="3,247"
          change={-2.3}
          icon={Users}
          trend="down"
        />
        <StatsCard
          title="API Calls"
          value="89.3K"
          change={18.2}
          icon={Activity}
          trend="up"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Articles Over Time */}
        <ComponentErrorBoundary>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Articles Collected Over Time</h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="month" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: 'none',
                    borderRadius: '8px'
                  }}
                  labelStyle={{ color: '#f3f4f6' }}
                />
                <Area
                  type="monotone"
                  dataKey="articles"
                  stroke="#f59e0b"
                  fill="#fbbf24"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </ComponentErrorBoundary>

        {/* Topic Distribution */}
        <ComponentErrorBoundary>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Topic Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={topicDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {topicDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </ComponentErrorBoundary>
      </div>

      {/* Sentiment Analysis */}
      <ComponentErrorBoundary>
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Sentiment Analysis - Last 7 Days</h3>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={sentimentTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="date" stroke="#6b7280" />
              <YAxis stroke="#6b7280" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: 'none',
                  borderRadius: '8px'
                }}
                labelStyle={{ color: '#f3f4f6' }}
              />
              <Legend />
              <Bar dataKey="positive" stackId="a" fill="#10b981" name="Positive" />
              <Bar dataKey="neutral" stackId="a" fill="#6b7280" name="Neutral" />
              <Bar dataKey="negative" stackId="a" fill="#ef4444" name="Negative" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </ComponentErrorBoundary>

      {/* Source Status Grid */}
      <ComponentErrorBoundary>
        <div>
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Data Source Status</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <SourceStatus />
          </div>
        </div>
      </ComponentErrorBoundary>

      {/* Recent Activity Feed */}
      <ComponentErrorBoundary>
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Recent Activity</h3>
          <div className="space-y-3">
            <ActivityItem
              type="news"
              title="El Tiempo: New economic measures announced"
              time="2 minutes ago"
            />
            <ActivityItem
              type="api"
              title="DANE API: Population statistics updated"
              time="15 minutes ago"
            />
            <ActivityItem
              type="analysis"
              title="Sentiment analysis completed for 500 articles"
              time="1 hour ago"
            />
            <ActivityItem
              type="news"
              title="Semana: Political developments in Bogotá"
              time="2 hours ago"
            />
          </div>
        </div>
      </ComponentErrorBoundary>
      </div>
    </RouteErrorBoundary>
  )
}

function ActivityItem({ type, title, time }: { type: string; title: string; time: string }) {
  const getIcon = () => {
    switch(type) {
      case 'news': return <FileText className="w-4 h-4" />
      case 'api': return <Database className="w-4 h-4" />
      case 'analysis': return <TrendingUp className="w-4 h-4" />
      default: return <Activity className="w-4 h-4" />
    }
  }

  const getColor = () => {
    switch(type) {
      case 'news': return 'text-blue-500'
      case 'api': return 'text-green-500'
      case 'analysis': return 'text-purple-500'
      default: return 'text-gray-500'
    }
  }

  return (
    <div className="flex items-start space-x-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors">
      <div className={`mt-0.5 ${getColor()}`}>
        {getIcon()}
      </div>
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-900 dark:text-white">{title}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400">{time}</p>
      </div>
    </div>
  )
}