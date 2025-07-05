import React, { useState, useEffect } from 'react';

const PlansPage = ({ backendUrl, user, token }) => {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/plans`);
      const data = await response.json();
      setPlans(data.plans);
    } catch (error) {
      console.error('Error fetching plans:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading plans...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900">Choose Your Plan</h2>
        <p className="text-gray-600 mt-2">Select the perfect plan for your AI visibility tracking needs</p>
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-green-800 font-medium">🎉 Current Plan: ENTERPRISE (Full Access!)</p>
          <p className="text-green-600 text-sm">Domain: futureseo.io (Ready for deployment!)</p>
          <p className="text-green-600 text-sm">✓ 1,500 scans/month • ✓ 10 brands • ✓ All features unlocked</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-7xl mx-auto">
        {plans.map((plan) => (
          <div
            key={plan.id}
            className={`relative bg-white p-8 rounded-2xl shadow-lg border-2 ${
              plan.popular ? 'border-blue-500 transform scale-105' : 'border-gray-200'
            } ${plan.id === 'enterprise' ? 'bg-gradient-to-br from-purple-50 to-blue-50' : ''}`}
          >
            {plan.popular && (
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                <span className="bg-blue-500 text-white px-4 py-2 rounded-full text-sm font-medium">
                  Most Popular
                </span>
              </div>
            )}

            {plan.id === 'enterprise' && (
              <div className="absolute -top-4 right-4">
                <span className="bg-green-500 text-white px-3 py-1 rounded-full text-xs font-medium">
                  ACTIVE
                </span>
              </div>
            )}

            <div className="text-center">
              <h3 className="text-2xl font-bold text-gray-900">{plan.name}</h3>
              <div className="mt-4 flex items-baseline justify-center">
                <span className="text-5xl font-extrabold text-gray-900">${plan.price}</span>
                <span className="ml-1 text-xl text-gray-500">/{plan.interval}</span>
              </div>
              <p className="mt-2 text-gray-500">{plan.scans} AI scans per month</p>
            </div>

            <ul className="mt-8 space-y-4">
              {plan.features.map((feature, index) => (
                <li key={index} className="flex items-center">
                  <svg className="h-5 w-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span className="text-gray-600">{feature}</span>
                </li>
              ))}
            </ul>

            <div className="mt-8">
              {plan.id === 'enterprise' ? (
                <button className="w-full bg-green-100 text-green-700 py-3 px-4 rounded-lg font-medium cursor-not-allowed">
                  ✓ Current Plan - Full Access
                </button>
              ) : (
                <button className="w-full bg-gray-100 text-gray-500 py-3 px-4 rounded-lg font-medium cursor-not-allowed">
                  Available Plan
                </button>
              )}
            </div>

            {plan.id === 'enterprise' && (
              <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-green-800 text-sm font-medium">🚀 Perfect for futureseo.io!</p>
                <p className="text-green-600 text-xs">Full feature testing + enterprise capabilities</p>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Feature Comparison */}
      <div className="mt-12 bg-white p-8 rounded-xl border border-gray-200">
        <h3 className="text-xl font-bold text-gray-900 mb-6">Feature Comparison</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 text-gray-900 font-medium">Feature</th>
                <th className="text-center py-3 text-gray-900 font-medium">Basic</th>
                <th className="text-center py-3 text-gray-900 font-medium">Pro</th>
                <th className="text-center py-3 text-gray-900 font-medium">Enterprise</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              <tr>
                <td className="py-4 text-gray-600">AI Platforms</td>
                <td className="py-4 text-center text-gray-600">ChatGPT only</td>
                <td className="py-4 text-center text-green-600">✓ All platforms</td>
                <td className="py-4 text-center text-green-600 font-bold">✓ All platforms</td>
              </tr>
              <tr>
                <td className="py-4 text-gray-600">Brands</td>
                <td className="py-4 text-center text-gray-600">1</td>
                <td className="py-4 text-center text-gray-600">3</td>
                <td className="py-4 text-center text-green-600 font-bold">10</td>
              </tr>
              <tr>
                <td className="py-4 text-gray-600">Monthly Scans</td>
                <td className="py-4 text-center text-gray-600">50</td>
                <td className="py-4 text-center text-gray-600">300</td>
                <td className="py-4 text-center text-green-600 font-bold">1,500</td>
              </tr>
              <tr>
                <td className="py-4 text-gray-600">Competitor Analysis</td>
                <td className="py-4 text-center text-gray-400">✗</td>
                <td className="py-4 text-center text-green-600">✓</td>
                <td className="py-4 text-center text-green-600 font-bold">✓ Advanced</td>
              </tr>
              <tr>
                <td className="py-4 text-gray-600">Weekly Recommendations</td>
                <td className="py-4 text-center text-gray-400">✗</td>
                <td className="py-4 text-center text-green-600">✓</td>
                <td className="py-4 text-center text-green-600 font-bold">✓ Custom</td>
              </tr>
              <tr>
                <td className="py-4 text-gray-600">Team Collaboration</td>
                <td className="py-4 text-center text-gray-400">✗</td>
                <td className="py-4 text-center text-gray-400">✗</td>
                <td className="py-4 text-center text-green-600 font-bold">✓ Full Access</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Domain Info */}
      <div className="mt-8 p-6 bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-xl">
        <div className="flex items-center space-x-4">
          <div className="text-4xl">🌐</div>
          <div>
            <h4 className="font-bold text-gray-900">🎉 Ready for futureseo.io Deployment!</h4>
            <p className="text-gray-600">Your Enterprise plan gives you full access to test all features before going live.</p>
            <div className="mt-2 flex space-x-4 text-sm">
              <span className="bg-green-100 text-green-700 px-2 py-1 rounded">✓ 1,500 scans/month</span>
              <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded">✓ 10 brands</span>
              <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded">✓ All features</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlansPage;