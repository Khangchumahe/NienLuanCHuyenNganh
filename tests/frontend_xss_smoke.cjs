const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync('static/js/app.js', 'utf8');
const portalSource = fs.readFileSync('templates/customer_portal.html', 'utf8');
const escapeFunction = source.match(/function escapeHtml\(text\)\s*\{[\s\S]*?\n\}/)?.[0];
const imageFunction = source.match(/function safeImageUrl\(url\)\s*\{[\s\S]*?\n\}/)?.[0];
const numberFunction = source.match(/function safeNumber\(value\)\s*\{[\s\S]*?\n\}/)?.[0];
assert.ok(escapeFunction, 'escapeHtml helper exists');
assert.ok(imageFunction, 'safeImageUrl helper exists');
assert.ok(numberFunction, 'safeNumber helper exists');
const portalNumberFunction = portalSource.match(/function safeNumber\(value\)\s*\{[\s\S]*?\n    \}/)?.[0];
assert.ok(portalNumberFunction, 'customer portal safeNumber helper exists');

const sandbox = {};
vm.createContext(sandbox);
vm.runInContext(`${escapeFunction}\n${imageFunction}\n${numberFunction}\nglobalThis.escapeHtml = escapeHtml; globalThis.safeImageUrl = safeImageUrl; globalThis.safeNumber = safeNumber;`, sandbox);

const payload = '<img src=x onerror=alert(1)>';
assert.equal(sandbox.escapeHtml(payload), '&lt;img src=x onerror=alert(1)&gt;');
assert.equal(sandbox.safeImageUrl('javascript:alert(1)'), '/static/img/product-placeholder.svg');
assert.equal(sandbox.safeImageUrl('https://example.org/item.png'), 'https://example.org/item.png');
const serverNumericHtml = '<img src=x onerror=alert(1)>';
assert.equal(sandbox.safeNumber(serverNumericHtml), 0);
assert.equal(String(sandbox.safeNumber(serverNumericHtml)).includes('<'), false);
const portalSandbox = {};
vm.createContext(portalSandbox);
vm.runInContext(`${portalNumberFunction}\nglobalThis.safeNumber = safeNumber;`, portalSandbox);
assert.equal(portalSandbox.safeNumber(serverNumericHtml), 0);
assert.match(portalSource, /function safeNumber\(value\)/, 'customer portal has safeNumber helper');
assert.match(portalSource, /SL \$\{safeNumber\(item\.quantity\)\}/, 'cart quantity is numeric-safe');
assert.match(portalSource, /data-remove="\$\{safeNumber\(index\)\}"/, 'cart index is numeric-safe');
assert.match(portalSource, /safeNumber\(product\.discount_price\)/, 'discount price is numeric-safe');
assert.match(portalSource, /safeNumber\(product\.price\)/, 'product price is numeric-safe');
assert.match(portalSource, /safeNumber\(variant\.stock_quantity\)/, 'variant stock is numeric-safe');
assert.match(portalSource, /safeNumber\(item\.quantity\)/, 'order quantity is numeric-safe');
assert.match(portalSource, /money\(safeNumber\(item\.subtotal\)\)/, 'order subtotal is numeric-safe');
console.log('Frontend XSS smoke checks passed.');
