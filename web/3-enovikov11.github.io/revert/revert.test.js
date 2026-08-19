const { test, expect } = require('@jest/globals');
const revertAlgo = require('./revert');

describe('revertAlgo', () => {
    test('empty', () => {
        expect(revertAlgo('')).toEqual('');
    });

    test('num', () => {
        expect(revertAlgo('123')).toEqual('123');
    });

    test('str', () => {
        expect(revertAlgo('abc')).toEqual('cba');
    });

    test('combined', () => {
        expect(revertAlgo('jbdh16jv!go')).toEqual('ogvj16hd!bj');
    });
});