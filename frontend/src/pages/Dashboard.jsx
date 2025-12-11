import React from 'react'
import { Link } from 'react-router-dom'
import { FileText, TestTube2, Sparkles, TrendingUp, ListChecks } from 'lucide-react'

export default function Dashboard() {
  const features = [
    {
      icon: FileText,
      title: 'Epic Analysis',
      description: 'Analyze Epics and generate test tickets using multi-agent AI',
      link: '/epic-analysis',
      color: 'from-blue-500 to-cyan-500'
    },
    {
      icon: ListChecks,
      title: 'Test Tickets',
      description: 'View and manage all generated test tickets from Epic analysis',
      link: '/test-tickets',
      color: 'from-green-500 to-emerald-500'
    },
    {
      icon: Sparkles,
      title: 'Ticket Improver',
      description: 'Enhance Jira tickets with clearer acceptance criteria and comprehensive details',
      link: '/ticket-improver',
      color: 'from-purple-500 to-pink-500'
    },
    {
      icon: TestTube2,
      title: 'Test Generation',
      description: 'Generate comprehensive test cases from Jira tickets',
      link: '/test-generation',
      color: 'from-orange-500 to-red-500'
    }
  ]

  const stats = [
    { label: 'Multi-Agent System', value: 'Active', icon: Sparkles },
    { label: 'AI Model', value: 'GPT-4o', icon: TrendingUp },
  ]

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-100 mb-2">Welcome to AI Tester Framework</h1>
        <p className="text-gray-400">
          AI-powered test case generation and Epic analysis with multi-agent orchestration
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        {stats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <div
              key={index}
              className="bg-dark-900 border border-dark-800 rounded-xl p-6 flex items-center space-x-4"
            >
              <div className="p-3 bg-primary-500/10 rounded-lg">
                <Icon className="text-primary-500" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-400">{stat.label}</p>
                <p className="text-xl font-semibold text-gray-100">{stat.value}</p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {features.map((feature, index) => {
          const Icon = feature.icon
          return (
            <Link
              key={index}
              to={feature.link}
              className="group bg-dark-900 border border-dark-800 rounded-xl p-8 hover:border-primary-500 transition-all hover:shadow-nebula-lg"
            >
              <div className={`w-16 h-16 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                <Icon className="text-white" size={32} />
              </div>
              <h3 className="text-xl font-semibold text-gray-100 mb-2 group-hover:text-primary-400 transition-colors">
                {feature.title}
              </h3>
              <p className="text-gray-400">{feature.description}</p>
            </Link>
          )
        })}
      </div>

      {/* Info Section */}
      <div className="bg-gradient-to-r from-primary-900/20 to-purple-900/20 border border-primary-800/30 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-primary-300 mb-2">Multi-Agent System v3.0</h3>
        <p className="text-gray-400 mb-4">
          Our advanced multi-agent architecture employs specialized AI agents throughout the entire testing lifecycle.
          From epic analysis and strategic planning to test ticket generation, coverage review, and detailed test case creation,
          each agent brings focused expertise to ensure comprehensive coverage and high-quality outputs.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="bg-dark-900/50 rounded-lg p-3">
            <h4 className="font-medium text-primary-400 mb-1 text-sm">Strategic Planner</h4>
            <p className="text-xs text-gray-400">Analyzes Epics and proposes test splitting strategies</p>
          </div>
          <div className="bg-dark-900/50 rounded-lg p-3">
            <h4 className="font-medium text-primary-400 mb-1 text-sm">Evaluator</h4>
            <p className="text-xs text-gray-400">Scores strategic options on quality metrics</p>
          </div>
          <div className="bg-dark-900/50 rounded-lg p-3">
            <h4 className="font-medium text-primary-400 mb-1 text-sm">Questioner</h4>
            <p className="text-xs text-gray-400">Identifies gaps and asks clarifying questions</p>
          </div>
          <div className="bg-dark-900/50 rounded-lg p-3">
            <h4 className="font-medium text-primary-400 mb-1 text-sm">Gap Analyzer</h4>
            <p className="text-xs text-gray-400">Analyzes and prioritizes requirement gaps</p>
          </div>
          <div className="bg-dark-900/50 rounded-lg p-3">
            <h4 className="font-medium text-primary-400 mb-1 text-sm">Test Ticket Generator</h4>
            <p className="text-xs text-gray-400">Creates comprehensive test tickets from epics</p>
          </div>
          <div className="bg-dark-900/50 rounded-lg p-3">
            <h4 className="font-medium text-primary-400 mb-1 text-sm">Test Ticket Reviewer</h4>
            <p className="text-xs text-gray-400">Reviews and validates test ticket quality</p>
          </div>
          <div className="bg-dark-900/50 rounded-lg p-3">
            <h4 className="font-medium text-primary-400 mb-1 text-sm">Coverage Reviewer</h4>
            <p className="text-xs text-gray-400">Evaluates test coverage completeness</p>
          </div>
          <div className="bg-dark-900/50 rounded-lg p-3">
            <h4 className="font-medium text-primary-400 mb-1 text-sm">Requirements Fixer</h4>
            <p className="text-xs text-gray-400">Generates fixes for coverage gaps</p>
          </div>
          <div className="bg-dark-900/50 rounded-lg p-3">
            <h4 className="font-medium text-primary-400 mb-1 text-sm">Ticket Analyzer</h4>
            <p className="text-xs text-gray-400">Assesses ticket readiness for test case generation</p>
          </div>
          <div className="bg-dark-900/50 rounded-lg p-3">
            <h4 className="font-medium text-primary-400 mb-1 text-sm">Test Case Generator</h4>
            <p className="text-xs text-gray-400">Creates detailed test cases from tickets</p>
          </div>
          <div className="bg-dark-900/50 rounded-lg p-3">
            <h4 className="font-medium text-primary-400 mb-1 text-sm">Test Case Critic</h4>
            <p className="text-xs text-gray-400">Reviews test cases for quality and completeness</p>
          </div>
          <div className="bg-dark-900/50 rounded-lg p-3">
            <h4 className="font-medium text-primary-400 mb-1 text-sm">Test Case Fixer</h4>
            <p className="text-xs text-gray-400">Improves test cases based on critic feedback</p>
          </div>
          <div className="bg-dark-900/50 rounded-lg p-3">
            <h4 className="font-medium text-primary-400 mb-1 text-sm">Test Case Reviewer</h4>
            <p className="text-xs text-gray-400">Analyzes and suggests additional test cases</p>
          </div>
          <div className="bg-dark-900/50 rounded-lg p-3">
            <h4 className="font-medium text-primary-400 mb-1 text-sm">Ticket Improver</h4>
            <p className="text-xs text-gray-400">Enhances tickets with detailed context and ACs</p>
          </div>
        </div>
      </div>
    </div>
  )
}
