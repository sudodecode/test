const { execSync } = require('child_process');

function listFiles(userInput) {
  return execSync('ls ' + userInput).toString();
}

module.exports = { listFiles };
