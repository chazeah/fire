import 'core-js/es6';
import 'core-js/es7/reflect';
import 'hammerjs/hammer';
import 'normalize.css/normalize.css';
require('zone.js/dist/zone');
require('promise.prototype.finally').shim();

if (process.env.ENV === 'production') {
    // Production
} else {
    // Development and test
    Error['stackTraceLimit'] = Infinity;
    require('zone.js/dist/long-stack-trace-zone');
}

