from utils.tools import gas_checker, repeater
from config import ZEROLEND_CONTRACTS, ZEROLEND_ABI, TOKENS_PER_CHAIN
from modules import Landing


class ZeroLend(Landing):
    def __init__(self, client):
        self.client = client

        self.landing_contract = self.client.get_contract(ZEROLEND_CONTRACTS['landing'], ZEROLEND_ABI)
        self.collateral_contract = self.client.get_contract(ZEROLEND_CONTRACTS['pool_proxy'], ZEROLEND_ABI)

    @repeater
    @gas_checker
    async def deposit(self):

        amount, amount_in_wei = await self.client.check_and_get_eth_for_deposit()

        self.client.logger.info(f'{self.client.info} Deposit to ZeroLend: {amount} ETH')

        tx_params = await self.client.prepare_transaction(value=amount_in_wei)

        transaction = await self.landing_contract.functions.depositETH(
            ZEROLEND_CONTRACTS['pool_proxy'],
            self.client.address,
            0
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    @repeater
    @gas_checker
    async def withdraw(self):
        self.client.logger.info(f'{self.client.info} Withdraw liquidity from ZeroLend')

        liquidity_balance = await self.client.get_contract(ZEROLEND_CONTRACTS['weth_atoken']).functions.balanceOf(
            self.client.address).call()

        if liquidity_balance != 0:

            await self.client.check_for_approved(ZEROLEND_CONTRACTS['weth_atoken'], ZEROLEND_CONTRACTS['landing'],
                                                 liquidity_balance)

            tx_params = await self.client.prepare_transaction()

            transaction = await self.landing_contract.functions.withdrawETH(
                ZEROLEND_CONTRACTS['pool_proxy'],
                liquidity_balance,
                self.client.address
            ).build_transaction(tx_params)

            return await self.client.send_transaction(transaction)

        else:
            raise RuntimeError('Insufficient balance on ZeroLend!')

    @repeater
    @gas_checker
    async def enable_collateral(self):
        self.client.logger.info(f'{self.client.info} Enable collateral on ZeroLend')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.collateral_contract.functions.setUserUseReserveAsCollateral(
            TOKENS_PER_CHAIN[self.client.network.name]['ETH'],
            True
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)

    @repeater
    @gas_checker
    async def disable_collateral(self):
        self.client.logger.info(f'{self.client.info} Disable collateral on ZeroLend')

        tx_params = await self.client.prepare_transaction()

        transaction = await self.collateral_contract.functions.setUserUseReserveAsCollateral(
            TOKENS_PER_CHAIN[self.client.network.name]['ETH'],
            False
        ).build_transaction(tx_params)

        return await self.client.send_transaction(transaction)