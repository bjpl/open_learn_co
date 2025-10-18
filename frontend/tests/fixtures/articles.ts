/**
 * Test Fixtures - Articles
 * Mock data for article-related tests
 */

export const mockArticle = {
  id: '1',
  title: 'Test Article Title',
  summary: 'This is a test article summary',
  content: 'Full article content goes here',
  source: 'El Tiempo',
  sourceUrl: 'https://example.com/article',
  publishedAt: '2024-01-15T10:00:00Z',
  category: 'Politics',
  sentiment: 0.65,
  difficulty: 'intermediate',
  language: 'es',
  imageUrl: 'https://example.com/image.jpg',
  tags: ['colombia', 'politics', 'economy'],
}

export const mockArticles = [
  mockArticle,
  {
    ...mockArticle,
    id: '2',
    title: 'Second Test Article',
    category: 'Economy',
    sentiment: 0.45,
  },
  {
    ...mockArticle,
    id: '3',
    title: 'Third Test Article',
    category: 'Social',
    sentiment: -0.2,
    difficulty: 'beginner',
  },
]

export const mockArticleFilters = {
  dateRange: {
    start: '2024-01-01',
    end: '2024-01-31',
  },
  categories: ['Politics', 'Economy'],
  sentiment: 'positive',
  difficulty: 'intermediate',
  sources: ['El Tiempo', 'Semana'],
  searchQuery: '',
  sortBy: 'date' as const,
  sortOrder: 'desc' as const,
}
