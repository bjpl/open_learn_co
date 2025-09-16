import { ArrowUp, ArrowDown, LucideIcon } from 'lucide-react'

interface StatsCardProps {
  title: string
  value: string | number
  change: number
  icon: LucideIcon
  trend: 'up' | 'down'
}

export default function StatsCard({ title, value, change, icon: Icon, trend }: StatsCardProps) {
  const isPositive = trend === 'up'

  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{value}</p>
          <div className="flex items-center mt-2">
            {isPositive ? (
              <ArrowUp className="w-4 h-4 text-green-500 mr-1" />
            ) : (
              <ArrowDown className="w-4 h-4 text-red-500 mr-1" />
            )}
            <span className={`text-sm ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
              {Math.abs(change)}%
            </span>
          </div>
        </div>
        <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
          <Icon className="w-6 h-6 text-yellow-600 dark:text-yellow-500" />
        </div>
      </div>
    </div>
  )
}