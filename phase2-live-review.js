const { execFileSync } = require('child_process');

function listFiles(userInput) {
  return execFileSync('ls', [userInput]).toString();
}

module.exports = { listFiles };
// review-on-push edge-case probe
