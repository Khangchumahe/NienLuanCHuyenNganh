const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync('static/js/app.js', 'utf8');
const escapeFunction = source.match(/function escapeHtml\(text\)\s*\{[\s\S]*?\n\}/)?.[0];
const imageFunction = source.match(/function safeImageUrl\(url\)\s*\{[\s\S]*?\n\}/)?.[0];
assert.ok(escapeFunction, 'escapeHtml helper exists');
assert.ok(imageFunction, 'safeImageUrl helper exists');

const sandbox = {};
vm.createContext(sandbox);
vm.runInContext(`${escapeFunction}\n${imageFunction}\nglobalThis.escapeHtml = escapeHtml; globalThis.safeImageUrl = safeImageUrl;`, sandbox);

const payload = '<img src=x onerror=alert(1)>';
assert.equal(sandbox.escapeHtml(payload), '&lt;img src=x onerror=alert(1)&gt;');
assert.equal(sandbox.safeImageUrl('javascript:alert(1)'), '/static/img/product-placeholder.svg');
assert.equal(sandbox.safeImageUrl('https://example.org/item.png'), 'https://example.org/item.png');
console.log('Frontend XSS smoke checks passed.');
