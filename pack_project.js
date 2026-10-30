// pack_project.js
const fs = require('fs');
const path = require('path');

// Output file name
const OUTPUT_FILE = 'project_code_dump.txt';

// Folders to ignore
const IGNORED_DIRS = new Set([
  'node_modules',
  '.venv',
  'venv',
  '__pycache__',
  '.git',
  '.vscode',
  'dist',
  'build'
]);

// Exact files to ignore
const IGNORED_FILES = new Set([
  OUTPUT_FILE,
  'pack_project.js',
  'package-lock.json',
  'adsense_ai.db',
  '.DS_Store',
  'Thumbs.db'
]);

// File extensions to ignore (images, databases, binaries, compiled cache)
const IGNORED_EXTENSIONS = new Set([
  '.png', '.jpg', '.jpeg', '.gif', '.ico', '.webp',
  '.db', '.sqlite', '.sqlite3',
  '.exe', '.bin', '.dll', '.so',
  '.pyc', '.zip', '.tar', '.gz', '.pdf'
]);

/**
 * Checks whether a file or directory should be ignored.
 */
function shouldIgnore(name, fullPath, isDirectory) {
  if (isDirectory) {
    return IGNORED_DIRS.has(name);
  }
  if (IGNORED_FILES.has(name)) {
    return true;
  }
  const ext = path.extname(name).toLowerCase();
  return IGNORED_EXTENSIONS.has(ext);
}

/**
 * Generates an ASCII visual tree of the directory structure.
 */
function generateTree(currentPath, prefix = '') {
  let output = '';
  const entries = fs.readdirSync(currentPath, { withFileTypes: true });

  const validEntries = entries.filter((entry) => {
    return !shouldIgnore(
      entry.name,
      path.join(currentPath, entry.name),
      entry.isDirectory()
    );
  });

  validEntries.forEach((entry, index) => {
    const isLast = index === validEntries.length - 1;
    const pointer = isLast ? '└── ' : '├── ';
    output += `${prefix}${pointer}${entry.name}\n`;

    if (entry.isDirectory()) {
      const nextPrefix = prefix + (isLast ? '    ' : '│   ');
      output += generateTree(path.join(currentPath, entry.name), nextPrefix);
    }
  });

  return output;
}

/**
 * Recursively collects all text and code files.
 */
function collectFiles(currentPath, rootPath, filesList = []) {
  const entries = fs.readdirSync(currentPath, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(currentPath, entry.name);

    if (shouldIgnore(entry.name, fullPath, entry.isDirectory())) {
      continue;
    }

    if (entry.isDirectory()) {
      collectFiles(fullPath, rootPath, filesList);
    } else {
      filesList.push(fullPath);
    }
  }

  return filesList;
}

/**
 * Main execution.
 */
function main() {
  const rootDir = process.cwd();
  const outputPath = path.join(rootDir, OUTPUT_FILE);

  console.log('Generating project folder tree...');
  const tree = `PROJECT FOLDER STRUCTURE:\n${path.basename(rootDir)}/\n` + generateTree(rootDir);

  console.log('Collecting code files...');
  const files = collectFiles(rootDir, rootDir);

  let finalOutput = `${tree}\n\n` +
    '='.repeat(80) + '\n' +
    'PROJECT FILES CONTENT\n' +
    '='.repeat(80) + '\n\n';

  for (const file of files) {
    const relativePath = path.relative(rootDir, file).replace(/\\/g, '/');
    try {
      const content = fs.readFileSync(file, 'utf8');
      finalOutput += `\n/* ${'='.repeat(70)} */\n`;
      finalOutput += `/* FILE: ${relativePath} */\n`;
      finalOutput += `/* ${'='.repeat(70)} */\n\n`;
      finalOutput += content.trim() + '\n\n';
    } catch (err) {
      console.warn(`Could not read file (possibly binary): ${relativePath}`);
    }
  }

  fs.writeFileSync(outputPath, finalOutput, 'utf8');
  console.log(`Success! Project bundled into: ${OUTPUT_FILE}`);
}

main();