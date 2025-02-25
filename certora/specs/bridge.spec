////////////////////////////////////////////////////////////////////////////
//                       Imports and multi-contracts                      //
////////////////////////////////////////////////////////////////////////////
import "erc20.spec"

// Declaring aliases for contracts according to the format:
// using Target_Contract as Alias_Name
/************************
 *     L1 contracts     *
 ************************/
    using DummyERC20UnderlyingA_L1 as UNDERLYING_ASSET_A 
    using DummyERC20UnderlyingB_L1 as UNDERLYING_ASSET_B
    using ATokenWithPoolA_L1 as ATOKEN_A
    using ATokenWithPoolB_L1 as ATOKEN_B
    using DummyERC20RewardToken as REWARD_TOKEN
    using SymbolicLendingPoolL1 as LENDINGPOOL_L1
    using IncentivesControllerMock_L1 as incentivesController

/************************
 *     L2 contracts     *
 ************************/
    using BridgeL2Harness as BRIDGE_L2
    using StaticATokenA_L2 as STATIC_ATOKEN_A
    using StaticATokenB_L2 as STATIC_ATOKEN_B

// For referencing structs
    using BridgeHarness as Bridge

////////////////////////////////////////////////////////////////////////////
//                       Methods                                          //
////////////////////////////////////////////////////////////////////////////
// Declaring contracts' methods and summarizing them as needed
methods {
/**********************
 *     Bridge.sol     *
 **********************/
 // Note that some functions should only be called via BridgeHarness
 // e.g. withdraw(), invoked by the initiateWithdraw on L2.
    initialize(uint256, address, address, address[], uint256[])
    deposit(address, uint256, uint256, uint16, bool) returns (uint256) 
    withdraw(address, uint256, address, uint256, uint256, bool)
    updateL2State(address)
    receiveRewards(uint256, address, uint256)
    
/*************************
 *     BridgeHarness     *
 *************************/
    // Note that these methods take as args OR return the contract types that are written in comment to their right.
    // In CVL we contracts are addresses an therefore we demand return of an address
    getATokenOfUnderlyingAsset(address, address) returns (address) envfree
    getLendingPoolOfAToken(address) returns (address) envfree //(ILendingPool)
    _staticToDynamicAmount_Wrapper(uint256, address, address) envfree //(ILendingPool)
    _dynamicToStaticAmount_Wrapper(uint256, address, address) envfree //(ILendingPool)
    _computeRewardsDiff_Wrapper(uint256, uint256, uint256) envfree
    _getCurrentRewardsIndex_Wrapper(address) returns (uint256) 
    initiateWithdraw_L2(address, uint256, address, bool)
    bridgeRewards_L2(address, uint256)
    getUnderlyingAssetOfAToken(address) returns (address) envfree
    underlyingtoAToken(address) returns (address) => DISPATCHER(true)

/******************************
 *     IStarknetMessaging     *
 ******************************/
    // The methods of Bridge.sol that call this contract are being overridden to bypass the messaging communication.
    // Instead, we modeled the L2 side in solidity and made direct calls between the sides.

/************************
 *     ILendingPool     *
 ************************/
    // The lending pool used in the contract is encapsulated within a struct in IBridge.sol.
    // We point to direct calls to these methods using dispatchers. 
    deposit(address, uint256, address, uint16) => DISPATCHER(true)
    withdraw(address, uint256, address) returns (uint256) => DISPATCHER(true)
    getReserveNormalizedIncome(address) returns (uint256) => DISPATCHER(true)
    LENDINGPOOL_L1.liquidityIndexByAsset(address) returns (uint256) envfree


/*************************************************
 *     IATokenWithPool     *
 *************************************************/
    mint(address, uint256, uint256) returns (bool) => DISPATCHER(true)
    mint(address, uint256) returns (bool) => DISPATCHER(true)
    burn(address, address, uint256, uint256) => DISPATCHER(true)
    burn(address, uint256) returns (bool) => DISPATCHER(true)
    POOL() returns (address) => DISPATCHER(true)
    scaledTotalSupply() returns (uint256) => DISPATCHER(true)
    getIncentivesController() => DISPATCHER(true)
    ATOKEN_A.balanceOf_super(address) returns (uint256) envfree
/************************************
 *     IncentivesControllerMock     *
 ************************************/
    _rewardToken() returns (address) envfree => DISPATCHER(true)
    DISTRIBUTION_END() returns (uint256) => CONSTANT
    getRewardsVault() returns (address) => DISPATCHER(true)
    getAssetData(address) returns (uint256, uint256, uint256) => DISPATCHER(true)
    // Note that the sender of the funds here is RewardsVault which is arbitrary by default.
    // If any rule that count on the reward token balance, calls this method a `require RewardsVault != to` make sense to add
    claimRewards(address[], uint256, address) returns (uint256) => DISPATCHER(true)
    
/***************************
 *     BridgeL2Harness     *
 ***************************/
    BRIDGE_L2.l2RewardsIndexSetter(uint256)
    BRIDGE_L2.deposit(address, uint256, address) 
    BRIDGE_L2.initiateWithdraw(address, uint256, address, address, bool)
    BRIDGE_L2.bridgeRewards(address, address, uint256)
    BRIDGE_L2.claimRewards(address, address)
    BRIDGE_L2.l2RewardsIndex() returns (uint256) envfree
    BRIDGE_L2.getStaticATokenAddress(address) returns (address) envfree
    BRIDGE_L2.address2uint256(address) returns (uint256) envfree

/******************
 *     Tokens     *
 ******************/
    UNDERLYING_ASSET_ADDRESS() returns (address) => DISPATCHER(true)
    ATOKEN_A.UNDERLYING_ASSET_ADDRESS() returns (address) envfree
    ATOKEN_B.UNDERLYING_ASSET_ADDRESS() returns (address) envfree  
    claimRewards(address) returns (uint256) => DISPATCHER(true)
    getRewTokenAddress() returns (address) => rewardToken()

/******************
 *     Ray Math   *
 ******************/
 // See also notes at bottom of file (under "Summarizations")
 // Comment out the next two lines to remove the simplification,
 // and let the prover use the original library functions.
 
    rayMul(uint256 a, uint256 b) returns (uint256) => rayMulConst(a, b)
    rayDiv(uint256 a, uint256 b) returns (uint256) => rayDivConst(a, b)
}

////////////////////////////////////////////////////////////////////////////
//                       Definitions                                      //
////////////////////////////////////////////////////////////////////////////

// Definition of RAY unit
definition RAY() returns uint256 = 10^27;

// Used for the Ray math summarization.
// Effectively sets the liquidity index in L1 to be a constant, given
// by the following value.
// Note: if the summarization is not used, i.e. they are commented out,
// this value has no use.
definition myConstRayValue() returns uint256 = RAY()*4;

// The following definition shall be used later in some invariants,
// by filtering out the 'initialize' function.
definition excludeInitialize(method f) returns bool =
    f.selector != 
    initialize(uint256, address, address, address[], uint256[]).selector; 

// A filter for parametric rules.
// The functions receiveRewards and withdraw should not be called by an external user
// Unless a message was already sent, which we mock through the additional functions that
// call the L2 interface.
// Using this filter via:
// filtered{f -> messageSentFilter(f)} will reduce running time, by skipping the analysis
// of these functions.
definition messageSentFilter(method f) returns bool = 
    f.selector != receiveRewards(uint256, address, uint256).selector
    &&
    f.selector != withdraw(address, uint256, address, uint256, uint256, bool).selector;

////////////////////////////////////////////////////////////////////////////
//                       Rules                                            //
////////////////////////////////////////////////////////////////////////////

/*
    @Rule - a template for rule description:

    @Description: Significance of rule, property
        

    @Formula:
        {
            require something (pre-condition)
        }
            < call any function or specific function >
        {
            assert post-condition
        }

    @Note:
        Some notes about requirements or special consideration of the rule.
    @Link:
        Link to last verification report run of the rule.
*/

// Checks basic properties of withdrawal.
rule integrityOfWithdraw(address recipient){
    bool toUnderlyingAsset;
    uint256 staticAmount; 
    env e; calldataarg args;
    address underlying;
    address static;
    address aToken;
    uint256 l2RewardsIndex = BRIDGE_L2.l2RewardsIndex();
    
    setupTokens(underlying, aToken, static);
    setupUser(e.msg.sender);
    require recipient != aToken;
    require recipient != currentContract;

    uint256 underlyingBalanceBefore = tokenBalanceOf(e, underlying, recipient);
    uint256 aTokenBalanceBefore = tokenBalanceOf(e, aToken, recipient);
    uint256 rewardTokenBalanceBefore = tokenBalanceOf(e, REWARD_TOKEN, recipient);

    initiateWithdraw_L2(e, aToken, staticAmount, recipient, toUnderlyingAsset);

    uint256 underlyingBalanceAfter = tokenBalanceOf(e, underlying, recipient);
    uint256 aTokenBalanceAfter = tokenBalanceOf(e, aToken, recipient);
    uint256 rewardTokenBalanceAfter = tokenBalanceOf(e, REWARD_TOKEN, recipient);

    if (toUnderlyingAsset){
        assert 
        (underlyingBalanceAfter >= underlyingBalanceBefore) &&
        (aTokenBalanceAfter == aTokenBalanceBefore);
    }
    else {
        assert 
        (aTokenBalanceAfter >= aTokenBalanceBefore) &&
        (underlyingBalanceAfter == underlyingBalanceBefore);

    }
    assert rewardTokenBalanceAfter >= rewardTokenBalanceBefore;
}

// If a balance of tokens changed, then deposit or withdrawal must have been called.
rule balanceOfUnderlyingAssetChanged(method f, uint256 amount)
filtered{f -> messageSentFilter(f)} {
    env e;    
    address asset;
    address AToken;
    address static;
    address recipient;
    bool fromToUA;
    
    setupTokens(asset, AToken, static);
    setupUser(e.msg.sender);

    // Underlying asset balances of sender and recipient before call.
    uint256 recipientBalanceA1 = tokenBalanceOf(e, AToken, recipient);
    uint256 recipientBalanceU1 = tokenBalanceOf(e, asset, recipient);

    // Call any interface function 
    callFunctionSetParams(f, e, recipient, AToken, asset, amount, fromToUA);

    // Underlying asset balances of sender and recipient after call.
    uint256 recipientBalanceA2 = tokenBalanceOf(e, AToken, recipient);
    uint256 recipientBalanceU2 = tokenBalanceOf(e, asset, recipient);

    bool balancesChanged = !(
        recipientBalanceA1 == recipientBalanceA2 && 
        recipientBalanceU1 == recipientBalanceU2);

    assert balancesChanged =>
            (f.selector == deposit(address, uint256, uint256, uint16, bool).selector 
            ||
            f.selector == initiateWithdraw_L2(address, uint256, address, bool).selector)
            , "balanceOf changed";
}

// A call to deposit and a subsequent call to withdraw with the same amount of 
// staticATokens received, should yield the same original balance for the user.
// For underlying tokens, the condition is modified by a bound, since staticToDynamic is not inversible with dyanmicToStatic.
rule depositWithdrawReversed(uint256 amount)
{
    env eB; env eF;
    address Atoken; // AAVE Token
    address asset;  // underlying asset
    address static; // staticAToken
    uint256 l2Recipient = BRIDGE_L2.address2uint256(eB.msg.sender);
    uint16 referralCode;
    bool fromUA; // (deposit) from underlying asset
    bool toUA; // (withdraw) to underlying asset

    setupTokens(asset, Atoken, static);
    setupUser(eF.msg.sender);
    requireRayIndex(asset);
    require eF.msg.sender == eB.msg.sender;
    uint256 indexL1 = LENDINGPOOL_L1.liquidityIndexByAsset(asset);

    uint256 balanceU1 = tokenBalanceOf(eB, asset, eB.msg.sender);
    uint256 balanceA1 = tokenBalanceOf(eB, Atoken, eB.msg.sender);
    uint256 balanceS1 = tokenBalanceOf(eB, static, eB.msg.sender);
        uint256 staticAmount = deposit(eB, Atoken, l2Recipient, amount, referralCode, fromUA);
    /////////////////////////
    /*
    One can use these values (post-deposit pre-withdrawal) for debugging.
    uint256 balanceU2 = tokenBalanceOf(eB, asset, eB.msg.sender);
    uint256 balanceA2 = tokenBalanceOf(eB, Atoken, eB.msg.sender);
    uint256 balanceS2 = tokenBalanceOf(eB, static, eB.msg.sender);
    */
    /////////////////////////
        initiateWithdraw_L2(eF, Atoken, staticAmount, eF.msg.sender, toUA);
    uint256 balanceU3 = tokenBalanceOf(eF, asset, eF.msg.sender);
    uint256 balanceA3 = tokenBalanceOf(eF, Atoken, eF.msg.sender);
    uint256 balanceS3 = tokenBalanceOf(eF, static, eF.msg.sender);
    
    assert balanceS1 == balanceS3;
    assert fromUA == toUA => balanceU3 - balanceU1 <= (indexL1/RAY()+1)/2;
    assert fromUA == toUA => balanceA3 == balanceA1;
}

// Checks that the transitions between static to dynamic are inverses.
// Verified
rule dynamicToStaticInversible1(uint256 amount)
{
    // We assume both indexes (L1,L2) are represented in Ray (1e27).
    address asset;
    requireRayIndex(asset);
    uint256 dynm = _staticToDynamicAmount_Wrapper(amount, asset, LENDINGPOOL_L1);
    uint256 stat = _dynamicToStaticAmount_Wrapper(dynm, asset, LENDINGPOOL_L1);
    assert amount == stat;
}

// Checks that it isn't possible to gain from transforming dynamic to static
// and back.
// This is violated because the mul and div are not inverses of each other,
// therefore can lead to mul(div(a,b),b) > a (depends on remainder value).
rule dynamicToStaticInversible2(uint256 amount)
{
    // We assume both indexes (L1,L2) are represented in Ray (1e27).
    address asset;
    requireRayIndex(asset);
    uint256 indexL1 = LENDINGPOOL_L1.liquidityIndexByAsset(asset);
    uint256 stat = _dynamicToStaticAmount_Wrapper(amount, asset, LENDINGPOOL_L1);
    uint256 dynm = _staticToDynamicAmount_Wrapper(stat, asset, LENDINGPOOL_L1);
    // assert dynm <= amount;  // Violated
    assert dynm - amount <= (indexL1/RAY() + 1)/2; // Pass
}

// We make sure that the message sent booleans are always false,
// meaning that, according to our implementation, no external call can
// invoke receiveRewards and withdraw in Bridge.sol, but only through the 
// designated functions in the harnessed Bridge contract.
invariant alwaysUnSent(env e)
   !withdrawMessageStatus(e) && !bridgeRewardsMessageStatus(e)
    filtered{f -> messageSentFilter(f)}


// Check consistency of 'asset' being registered as the underlying
// token of 'AToken', both in the AToken contract, and also in the 
// mapping _aTokenData.
// We exclude the 'initialize' function since it is called only once
// in the code. 
invariant underlying2ATokenConsistency(address AToken, address asset)
     (asset !=0 <=> AToken !=0) 
     =>
     (getUnderlyingAssetHelper(AToken) == asset 
     <=>
     getUnderlyingAssetOfAToken(AToken) == asset)
     filtered{f-> excludeInitialize(f) && messageSentFilter(f)}

// Check consistency of 'asset' being registered as the underlying
// token of 'AToken', and 'AToken' connected to 'asset' in the lending pool.
// We exclude the 'initialize' function since it is called only once
// in the code. 
invariant ATokenAssetPair(address asset, address AToken)
    (asset !=0 <=> AToken !=0) 
    =>
    (getUnderlyingAssetHelper(AToken) == asset 
    <=>
    getATokenOfUnderlyingAsset(LENDINGPOOL_L1, asset) == AToken)
    filtered{f -> excludeInitialize(f)  && messageSentFilter(f)}

// The aToken-asset pair should be correctly registered after calling
// initialize, right after the constructor.
// This is complementary to the two invariants above.
rule initializeIntegrity(address AToken, address asset)
{
    env e;
    calldataarg args;

    // Post-constructor conditions
    require getUnderlyingAssetHelper(AToken) == 0;
    require getATokenOfUnderlyingAsset(LENDINGPOOL_L1, asset) == 0;
    
    initialize(e, args);

    assert (asset !=0 && AToken !=0) => (
        getUnderlyingAssetHelper(AToken) == asset 
        <=>
        getATokenOfUnderlyingAsset(LENDINGPOOL_L1, asset) == AToken);
}

// Sanity(f) - there exists a non-reverting path for a the contract method f.
// If the rule is verified (green V), no such path exists.
rule sanity(method f) {
    env e;
    address receiver;
    address aToken;
    address asset;
    address static;
    uint256 amount; 
    bool fromToUnderlyingAsset;
    setupTokens(asset, aToken, static);
    setupUser(e.msg.sender);
    callFunctionSetParams(f, e, receiver, aToken, asset, amount, fromToUnderlyingAsset);
    assert false;
}


rule depositIntegrity() {
    env e;
    address user;
    address Atoken; // AAVE Token
    address asset;  // underlying asset
    address static; // staticAToken
    uint256 l2Recipient = BRIDGE_L2.address2uint256(user);
    uint16 referralCode;
    bool fromUA; // (deposit) from underlying asset

    
    uint256 dynAmount; // amount of Atoken/asset tokens to deposit
    uint256 statAmount = _dynamicToStaticAmount_Wrapper(dynAmount, asset, LENDINGPOOL_L1);
    uint256 indexL1 = LENDINGPOOL_L1.liquidityIndexByAsset(asset);

    setupTokens(asset, Atoken, static);
    setupUser(user);
    requireRayIndex(asset);
    require user == e.msg.sender;


    uint256 userBalanceU1 = tokenBalanceOf(e, asset, user);
    uint256 userBalanceA1 = tokenBalanceOf(e, Atoken, user);
    uint256 userBalanceS1 = tokenBalanceOf(e, static, user);

    uint256 bridgeBalanceU1 = tokenBalanceOf(e, asset, Bridge);
    uint256 bridgeBalanceA1 = tokenBalanceOf(e, Atoken, Bridge);
    uint256 bridgeBalanceS1 = tokenBalanceOf(e, static, Bridge);

    uint256 ATokenBalanceU1 = tokenBalanceOf(e, asset, Atoken);


    uint256 depositAmount = deposit(e, Atoken, l2Recipient, dynAmount, referralCode, fromUA);

    uint256 userBalanceU2 = tokenBalanceOf(e, asset, user);
    uint256 userBalanceA2 = tokenBalanceOf(e, Atoken, user);
    uint256 userBalanceS2 = tokenBalanceOf(e, static, user);

    uint256 bridgeBalanceU2 = tokenBalanceOf(e, asset, Bridge);
    uint256 bridgeBalanceA2 = tokenBalanceOf(e, Atoken, Bridge);
    uint256 bridgeBalanceS2 = tokenBalanceOf(e, static, Bridge);

    uint256 ATokenBalanceU2 = tokenBalanceOf(e, asset, Atoken);


    assert depositAmount == statAmount;
    
    //if we're depositing underlying asset
    assert fromUA => 
        userBalanceU2   == userBalanceU1 - dynAmount && //user's underlying asset amount decreases
        ATokenBalanceU2 == ATokenBalanceU1 + dynAmount && //L1 aTokens are minted and aToken address is holding the underlying assets
        bridgeBalanceA2 - (bridgeBalanceA1 + dynAmount) <= (indexL1/RAY() + 1)/2 && //L1 aTokens are held by the L1 bridge contract
        userBalanceS2   == userBalanceS1 + statAmount && //static aTokens on L2 are received by the user
        userBalanceA2   == userBalanceA1 && //nothing should change here
        bridgeBalanceU2 == bridgeBalanceU1 && //nothing should change here
        bridgeBalanceS2 == bridgeBalanceS1; //nothing should change here

    //if we're depositing aTokens
     assert !fromUA =>
        userBalanceA2   - (userBalanceA1 + dynAmount) <= (indexL1/RAY() + 1)/2 && //user's amount of aTokens amount decreases
        bridgeBalanceA2 - (bridgeBalanceA1 + dynAmount) <= (indexL1/RAY() + 1)/2 && //L1 aTokens are send to the L1 bridge contract
        userBalanceS2   == userBalanceS1 + statAmount && //static aTokens on L2 are received by the user
        userBalanceU2   == userBalanceU1 && //nothing should change here
        bridgeBalanceU2 == bridgeBalanceU1 && //nothing should change here
        bridgeBalanceS2 == bridgeBalanceS1 && //nothing should change here
        ATokenBalanceU2 == ATokenBalanceU1; //nothing should change here
}


rule depositUA_EQ_depositAToken() {
    env e;
    address user;
    uint256 amount;
    address Atoken; // AAVE Token
    address asset;  // underlying asset
    address static; // staticAToken
    uint256 l2Recipient = BRIDGE_L2.address2uint256(user);
    uint16 referralCode;

    setupTokens(asset, Atoken, static);
    setupUser(user);
    requireRayIndex(asset);
    require user == e.msg.sender;

    storage initial = lastStorage;

    // depositing underlying asset
    deposit(e, Atoken, l2Recipient, amount, referralCode, true) at initial;

    uint256 bridgeBalanceA_depositUA = tokenBalanceOf(e, Atoken, Bridge);
    uint256 userBalanceS_depositUA   = tokenBalanceOf(e, static, user);

    // depositing aTokens
    deposit(e, Atoken, l2Recipient, amount, referralCode, false) at initial;

    uint256 bridgeBalanceA_depositAToken = tokenBalanceOf(e, Atoken, Bridge);
    uint256 userBalanceS_depositAToken   = tokenBalanceOf(e, static, user);

    /*
        No matter when depositing UL or aTokens:
            1. The new amount of aTokens of the L1 bridge should be the same
            2. The new amount of static aTokens on L2 side linked to the user should be the same
    */
    assert 
        bridgeBalanceA_depositUA == bridgeBalanceA_depositAToken &&
        userBalanceS_depositUA == userBalanceS_depositAToken;
}

rule withdrawRewardsFromL2Integrity() {
    env e;
    address user;
    address userRewardAddress;
    uint256 amount;
    address Atoken; // AAVE Token
    address asset;  // underlying asset
    address static; // staticAToken

    setupTokens(asset, Atoken, static);
    setupUser(user);
    setupUser(userRewardAddress);
    requireRayIndex(asset);
    require user == e.msg.sender;
    require user != userRewardAddress;


    uint256 rewardsL1Before = tokenBalanceOf(e, REWARD_TOKEN, userRewardAddress);
    uint256 rewardsL2Before = tokenBalanceOf(e, REWARD_TOKEN, user);

    // bridging rewards from L2 to L1
    bridgeRewards_L2(e, userRewardAddress, amount);

    uint256 rewardsL1After = tokenBalanceOf(e, REWARD_TOKEN, userRewardAddress);
    uint256 rewardsL2After = tokenBalanceOf(e, REWARD_TOKEN, user);

    assert rewardsL2After == rewardsL2Before - amount;

    assert rewardsL1After == rewardsL1Before + amount;
}


rule cantExtractAssetsFromL1WhenNoAssetsOnL2(method f) 
    filtered {   f -> messageSentFilter(f) &&
                 f.selector != deposit(address, uint256, uint256, uint16, bool).selector  
    } {
    
    env e;  
    address user;
    uint256 amount;
    address asset;
    address Atoken;
    address static;
    bool fromToUA;
    
    setupTokens(asset, Atoken, static);
    setupUser(user);
    require user == e.msg.sender;
    

    uint256 userBalanceU1 = tokenBalanceOf(e, asset, user);
    uint256 userBalanceA1 = tokenBalanceOf(e, Atoken, user);
    uint256 userBalanceS1 = tokenBalanceOf(e, static, user);

    callFunctionSetParams(f, e, user, Atoken, asset, amount, fromToUA);

    uint256 userBalanceU2 = tokenBalanceOf(e, asset, user);
    uint256 userBalanceA2 = tokenBalanceOf(e, Atoken, user);
    uint256 userBalanceS2 = tokenBalanceOf(e, static, user);

    /*
        If the user has no static tokens on L2, no function can alter the
            1. amount of underlying assets on L1
            2. amount of aTokens on L1
    */
    assert (userBalanceS1 == 0) =>
        userBalanceU1 == userBalanceU2 &&
        userBalanceA1 == userBalanceA2;
        
}


rule balanceStaticATokenOnlyChangesUponDepositOrWithdraw(method f) 
    filtered { f -> messageSentFilter(f) } {
    
    env e;  
    address user;
    uint256 amount;
    address asset;
    address Atoken;
    address static;
    bool fromToUA;
    
    setupTokens(asset, Atoken, static);
    setupUser(user);
    require user == e.msg.sender;
    require amount != 0;
    

    uint256 userBalanceS1 = tokenBalanceOf(e, static, user);

    callFunctionSetParams(f, e, user, Atoken, asset, amount, fromToUA);

    uint256 userBalanceS2 = tokenBalanceOf(e, static, user);

    /*
        If the amount of static tokens on L2 of a specific user...
            1. ... increases, the deposit function should have been called
            2. ... decreases, the withdraw function on L2 should have been called
    */

    assert userBalanceS1 < userBalanceS2 <=> 
        f.selector == deposit(address, uint256, uint256, uint16, bool).selector;
    
    assert userBalanceS1 > userBalanceS2 <=> 
        f.selector == initiateWithdraw_L2(address, uint256, address, bool).selector;
}






////////////////////////////////////////////////////////////////////////////
//                       Functions                                        //
////////////////////////////////////////////////////////////////////////////

// A general requirement set for the token trio:
// asset - underlying asset
// AToken - correpsonding AToken in the lending pool.
// static - staticAToken to be minted on L2.
function setupTokens(
    address asset, 
    address AToken, 
    address static){
    // Selects a dummy contract implementation for the tokens trio.
    // Note that if it used twice, for two different trios, it is possible
    // they will share the same addresses.
    tokenSelector(asset, AToken, static);
    // Links tokens to each other throught the bridges and pool stored data.
    setLinkage(asset, AToken, static);
    // Links asset and AToken. (Might be redundant after calling 'setLinkage').
    requireInvariant ATokenAssetPair(asset, AToken);
}

// A general requirement set for an extenral user using the bridge.
// User should usually be the msg.sender, but not necessarily the recipient!
function setupUser(address user){
    // Exclude contracts addresses from possible values of [user].
    requireValidUser(user);
}

// Selects specific instances for underlying asset, AToken and static tokens.
function tokenSelector(
    address asset, 
    address AToken, 
    address static){
    require asset == UNDERLYING_ASSET_A || asset == UNDERLYING_ASSET_B;
    require AToken == ATOKEN_A || AToken == ATOKEN_B;
    require static == STATIC_ATOKEN_A || static == STATIC_ATOKEN_B;
}

// By definition, the liquidity indexes are expressed in RAY units.
// Therefore they must be at least as large as RAY (assuming liquidity index > 1).
function requireRayIndex(address asset) {
    require LENDINGPOOL_L1.liquidityIndexByAsset(asset) >= RAY();
    require BRIDGE_L2.l2RewardsIndex() >= RAY();
}

// Require a constant value for the L1 index.
// Supposed to (hopefully) make runs faster, note that is reduces coverage!
function constantL1Index(address asset, uint256 value_in_Ray){
   require LENDINGPOOL_L1.liquidityIndexByAsset(asset) == value_in_Ray*RAY();
}

// Linking the instances of ERC20s and LendingPool 
// within the ATokenData struct to the corresponding symbolic contracts.
function setLinkage(
    address asset, 
    address AToken, 
    address static){
    // Setting the underlying token of the given AToken as either UNDERLYING_ASSET_A or UNDERLYING_ASSET_B
    require getUnderlyingAssetOfAToken(AToken) == asset;
    require getLendingPoolOfAToken(AToken) == LENDINGPOOL_L1;
    require BRIDGE_L2.getStaticATokenAddress(AToken) == static;
    setUnderlyingAToken(AToken, asset);
}

function setUnderlyingAToken(address AToken, address asset) {
    // Note that if AToken is neither ATOKEN_A nor ATOKEN_B,
    // this function will force asset == 0.
    require getUnderlyingAssetHelper(AToken) == asset;
}

function getUnderlyingAssetHelper(address AToken) returns address {
    if (AToken == ATOKEN_A) {
        return ATOKEN_A.UNDERLYING_ASSET_ADDRESS();
    }
    else if (AToken == ATOKEN_B) {
        return ATOKEN_B.UNDERLYING_ASSET_ADDRESS();
    }
    // Warning: default value is 0!
    return 0;
}

// Require the token trio (asset, Atoken, StaticAToken) to have
// distinct addresses.
function requireValidTokens(
    address asset, 
    address AToken, 
    address static){
        require asset != AToken &&
                AToken != static &&
                static != asset;
}

// Requirements for a "valid" user - exclude contracts addresses.
function requireValidUser(address user){
    require 
        user != Bridge &&
        user != BRIDGE_L2 &&
        user != UNDERLYING_ASSET_A &&
        user != UNDERLYING_ASSET_B &&
        user != ATOKEN_A &&
        user != ATOKEN_B &&
        user != STATIC_ATOKEN_A &&
        user != STATIC_ATOKEN_B &&
        user != REWARD_TOKEN &&
        user != LENDINGPOOL_L1 &&
        user != incentivesController;
}

// Returns the address of the reward token contract (used for summarization)
function rewardToken() returns address {
    return REWARD_TOKEN;
}

// A function selector helper, to specify the receiver.
function callFunctionSetParams(
    method f, env e, address receiver,
    address aToken, address asset,
    uint256 amount, bool fromToUnderlyingAsset) returns uint256 {
    // Inhibits the user from calling the functions withdraw and receiveRewards.
    // Expect unreachability for these functions (intended). 
    requireInvariant alwaysUnSent(e);
    if (f.selector == initiateWithdraw_L2(address, uint256, address, bool).selector){
        require receiver != currentContract;
        return initiateWithdraw_L2(e, aToken, amount, receiver, fromToUnderlyingAsset); 
    }   
    else if (f.selector == deposit(address, uint256, uint256, uint16, bool).selector){
        uint256 l2Recipient = BRIDGE_L2.address2uint256(receiver);
        uint16 referralCode;
        require receiver != currentContract;
        return deposit(e, aToken, l2Recipient, amount, referralCode, fromToUnderlyingAsset);
    }
    else if (f.selector == bridgeRewards_L2(address, uint256).selector) {
        bridgeRewards_L2(e, receiver, amount);
        return 0;
    }
    else {
        calldataarg args;
        f(e, args);
        return 0;
    }     
}

////////////////////////////////////////////////////////////////////////////
//                       Summarizations                                   //
////////////////////////////////////////////////////////////////////////////
/*
The following functions are used as summarization (under-approximation)
for the real functions in the code rayMul and rayDiv.
While the real functions assume any value for b,
here it is fixed by value to myConstRayValue() (a is not limited).
This dratically reduces coverage, but can still catch bugs related
to non-conservation of tokens.
The main benefit is the reduced runtime of rules.

To switch on/off the summarization, simply comment the lines
in the methods block of declaring these functions (127-128)
*/

function rayMulConst(uint256 a, uint256 b) returns uint256
{
    uint256 myValue = myConstRayValue();
    uint256 val_Ray = myConstRayValue()/RAY();
    require b == myValue;
    require a <= (max_uint - RAY()/2)/ myValue;
    return to_uint256(val_Ray*a);
}

function rayDivConst(uint256 a, uint256 b) returns uint256 
{
    uint256 myValue = myConstRayValue();
    uint256 val_Ray = myConstRayValue()/RAY();
    require b == myValue;
    require a <= (max_uint - myValue/2) / RAY();
    return to_uint256((2*a + val_Ray) / (2*val_Ray));
}
