const { execFileSync } = require('child_process');

function listFiles(userInput) {
  return execFileSync('ls', [userInput]).toString();
}

module.exports = { listFiles };
