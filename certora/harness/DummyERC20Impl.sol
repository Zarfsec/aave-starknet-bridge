// SPDX-License-Identifier: agpl-3.0
pragma solidity ^0.8.0;

contract DummyERC20Impl {
    uint256 t;
    mapping(address => uint256) b;
    mapping(address => mapping(address => uint256)) a;

    string public name;
    string public symbol;
    uint256 public decimals;

    constructor(){
        name = "dummy";
        symbol = "DUM";
    }

    function myAddress() public returns (address) {
        return address(this);
    }

    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        uint256 c = a + b;
        require(c >= a);
        return c;
    }

    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        require(a >= b);
        return a - b;
    }

    function totalSupply() public view virtual returns (uint256) {
        return t;
    }

    function balanceOf(address account) public view virtual returns (uint256) {
        return b[account];
    }

    function transfer(address recipient, uint256 amount)
        virtual external
        returns (bool)
    {
        b[msg.sender] = sub(b[msg.sender], amount);
        b[recipient] = add(b[recipient], amount);
        return true;
    }

    function allowance(address owner, address spender)
        external
        view
        returns (uint256)
    {
        return a[owner][spender];
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        a[msg.sender][spender] = amount;
        return true;
    }

    function transferFrom(
        address sender,
        address recipient,
        uint256 amount
    ) external virtual returns (bool) {
        b[sender] = sub(b[sender], amount);
        b[recipient] = add(b[recipient], amount);
        a[sender][msg.sender] = sub(a[sender][msg.sender], amount);
        return true;
    }
}
