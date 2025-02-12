import brownie
from brownie import Contract
from brownie import config
import math

# test the our strategy's ability to deposit, harvest, and withdraw, with different optimal deposit tokens if we have them
def test_simple_harvest(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    strategist_ms,
    gauge,
    rewardsContract,
    amount,
    sleep_time,
    convexToken,
    crv,
    usdc
):
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    newWhale = token.balanceOf(whale)

    # this is part of our check into the staking contract balance
    stakingBeforeHarvest = rewardsContract.balanceOf(strategy)

    # harvest, store asset amount
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    old_assets = vault.totalAssets()
    assert old_assets > 0
    assert token.balanceOf(strategy) == 0
    stratAssets = strategy.estimatedTotalAssets()
    assert stratAssets > 0
    print("\nStarting Assets: ", old_assets / 1e18)

    # try and include custom logic here to check that funds are in the staking contract (if needed)
    assert rewardsContract.balanceOf(strategy) > stakingBeforeHarvest

    # simulate profits
    chain.sleep(sleep_time)
    chain.mine(1)

    # harvest, store new asset amount
    chain.sleep(1)
    #make sure we have something to claim
    assert strategy.claimableBalance() > 0
    strategy.harvest({"from": gov})

    #make sure we claimed and sold all assets back into want
    assert strategy.claimableBalance() == 0
    chain.sleep(1)
    assert convexToken.balanceOf(strategy) == 0
    assert crv.balanceOf(strategy) == 0
    assert usdc.balanceOf(strategy) == 0
    new_assets = vault.totalAssets()
    # confirm we made money, or at least that we have about the same
    assert new_assets >= old_assets
    print("\nAssets after 1 day: ", new_assets / 1e18)

    # Display estimated APR
    print(
        "\nEstimated DAI APR: ",
        "{:.2%}".format(
            ((new_assets - old_assets) * (365 * 86400 / sleep_time))
            / (strategy.estimatedTotalAssets())
        ),
    )

    # store asset amount
    before_usdt_assets = vault.totalAssets()
    assert token.balanceOf(strategy) == 0
    assert strategy.estimatedTotalAssets() > 0
    assert token.balanceOf(vault) > 0

    # try and include custom logic here to check that funds are in the staking contract (if needed)
    assert rewardsContract.balanceOf(strategy) > 0

    # simulate profits
    chain.sleep(sleep_time)
    chain.mine(1)

    # harvest, store new asset amount
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    after_usdt_assets = vault.totalAssets()
    # confirm we made money, or at least that we have about the same
    assert after_usdt_assets >= before_usdt_assets

    # Display estimated APR
    print(
        "\nEstimated USDT APR: ",
        "{:.2%}".format(
            ((after_usdt_assets - before_usdt_assets) * (365 * 86400 / sleep_time))
            / (strategy.estimatedTotalAssets())
        ),
    )

    # simulate a day of waiting for share price to bump back up
    chain.sleep(86400)
    chain.mine(1)

    # withdraw and confirm we made money, or at least that we have about the same
    vault.withdraw({"from": whale})
    print(f"Vault locked {vault.lockedProfit()} strategy assets {strategy.estimatedTotalAssets()} vault pps {vault.pricePerShare()}")
    assert token.balanceOf(whale) >= startingWhale
