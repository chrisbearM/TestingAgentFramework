import React from 'react'
import { Link } from 'react-router-dom'
import { FileText, TestTube2, Sparkles, TrendingUp } from 'lucide-react'

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
      icon: TestTube2,
      title: 'Test Generation',
      description: 'Generate comprehensive test cases from Jira tickets',
      link: '/test-generation',
      color: 'from-purple-500 to-pink-500'
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
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
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
          Our new multi-agent architecture uses specialized AI agents for strategic planning, evaluation,
          and test generation. Each agent focuses on a specific aspect of the testing process,
          ensuring comprehensive coverage and high-quality outputs.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-dark-900/50 rounded-lg p-4">
            <h4 className="font-medium text-primary-400 mb-1">Strategic Planner</h4>
            <p className="text-sm text-gray-400">Analyzes Epics and proposes splitting strategies</p>
          </div>
          <div className="bg-dark-900/50 rounded-lg p-4">
            <h4 className="font-medium text-primary-400 mb-1">Evaluator</h4>
            <p className="text-sm text-gray-400">Scores options on quality metrics</p>
          </div>
          <div className="bg-dark-900/50 rounded-lg p-4">
            <h4 className="font-medium text-primary-400 mb-1">Test Generator</h4>
            <p className="text-sm text-gray-400">Creates detailed test cases with critics</p>
          </div>
        </div>
      </div>
    </div>
  )
}
