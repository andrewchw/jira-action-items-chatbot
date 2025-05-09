module.exports = {
  testEnvironment: 'jsdom',
  moduleFileExtensions: ['js', 'json'],
  transform: {
    '^.+\\.js$': 'babel-jest'
  },
  collectCoverage: true,
  collectCoverageFrom: [
    'popup/*.js',
    'content/*.js',
    'background.js'
  ],
  coverageDirectory: 'coverage',
}; 