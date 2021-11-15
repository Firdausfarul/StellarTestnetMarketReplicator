import json
import random
import time
import base64

#created by @firdausfarul
#somehow didn't work with sdk version 6.0.0 so use past version (5.0.0 or 5.0.1) instead

import stellar_sdk
from stellar_sdk import Keypair,Server, TransactionBuilder, Network, Signer, Asset, xdr
import requests

server = Server("https://horizon-testnet.stellar.org")
serverpublic=Server('https://horizon.stellar.org')
base_fee = server.fetch_base_fee()*1000

issuer_acc = Keypair.random() #Asset Issuer
marketmaker1_acc = Keypair.random() #Bids + LiquidityPool
marketmaker2_acc = Keypair.random() #Asks + LiquidityPool
trader_acc= Keypair.random() #Account loaded with the Asset

print('Issuer Account Public Key : ' + issuer_acc.public_key)
print('Issuer Account Secret Key : ' + issuer_acc.secret)
print('MarketMaker1 Account Public Key : ' + marketmaker1_acc.public_key)
print('MarketMaker1 Account Secret Key : ' + marketmaker1_acc.secret)
print('MarketMaker2 Account Public Key : ' + marketmaker2_acc.public_key)
print('MarketMaker2 Account Secret Key : ' + marketmaker2_acc.secret)
print('Trader Account Public Key : ' + trader_acc.public_key)
print('Trader Account Secret Key : ' + trader_acc.secret)

requests.get('https://friendbot.stellar.org?addr='+issuer_acc.public_key)
requests.get('https://friendbot.stellar.org?addr='+marketmaker1_acc.public_key)
requests.get('https://friendbot.stellar.org?addr='+marketmaker2_acc.public_key)
requests.get('https://friendbot.stellar.org?addr='+trader_acc.public_key)

#Asset You want to copy
XLM=Asset('XLM')
LSP=Asset('LSP','GAB7STHVD5BDH3EEYXPI3OM7PCS4V443PYB5FNT6CFGJVPDLMKDM24WK')
AQUA=Asset('AQUA','GBNZILSTVQZ4R7IKQDGHYGY2QXL5QOFJYQMXPKWRRM5PAV7Y4M67AQUA')
SLT=Asset('SLT','GCKA6K5PCQ6PNF5RQBF7PQDJWRHO6UOGFMRLK3DYHDOI244V47XKQ4GP')
TERN=Asset('TERN','GDGQDVO6XPFSY4NMX75A7AOVYCF5JYGW2SHCJJNWCQWIDGOZB53DGP6C')
USDC=Asset('USDC','GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN')
YBX=Asset('YBX','GBUYYBXWCLT2MOSSHRFCKMEDFOVSCAXNIEW424GLN666OEXHAAWBDYMX')

#Max 15 Asset due to 100 operations limit
IssuedAsset=[XLM, LSP, AQUA, SLT, TERN, USDC, YBX]
#doesn't matter too much
AmountIssued='100000000' #100 million

#Pair that you want to copy (XLM-USDC mean pairA=XLM pairB=USDC)
pairA=[XLM, XLM, XLM, AQUA, XLM]
pairB=[AQUA, YBX, LSP, USDC, TERN]

mm1_acc_loaded=server.load_account(marketmaker1_acc.public_key)

#Issuing Asset
IssueAsset=TransactionBuilder(
        source_account=mm1_acc_loaded,
        network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
        base_fee=base_fee,
    )
for i in range(len(IssuedAsset)):
    IssueAsset.append_change_trust_op(
        source=marketmaker1_acc.public_key,
        asset_code=IssuedAsset[i].code,
        asset_issuer=issuer_acc.public_key
    )
    IssueAsset.append_change_trust_op(
        source=marketmaker2_acc.public_key,
        asset_code=IssuedAsset[i].code,
        asset_issuer=issuer_acc.public_key
    )
    IssueAsset.append_change_trust_op(
        source=trader_acc.public_key,
        asset_code=IssuedAsset[i].code,
        asset_issuer=issuer_acc.public_key
    )
    IssueAsset.append_payment_op(
        source=issuer_acc.public_key,
        amount=AmountIssued,
        asset_code=IssuedAsset[i].code,
        asset_issuer=issuer_acc.public_key,
        destination=marketmaker1_acc.public_key,
    )
    IssueAsset.append_payment_op(
        source=issuer_acc.public_key,
        amount=AmountIssued,
        asset_code=IssuedAsset[i].code,
        asset_issuer=issuer_acc.public_key,
        destination=marketmaker2_acc.public_key,
    )
    IssueAsset.append_payment_op(
        source=issuer_acc.public_key,
        amount=AmountIssued,
        asset_code=IssuedAsset[i].code,
        asset_issuer=issuer_acc.public_key,
        destination=trader_acc.public_key,
    )

IssueAsset=IssueAsset.build()
IssueAsset.sign(issuer_acc.secret)
IssueAsset.sign(marketmaker1_acc.secret)
IssueAsset.sign(marketmaker2_acc.secret)
IssueAsset.sign(trader_acc.secret)
response=(server.submit_transaction(IssueAsset))
print('TxHash = '+response['hash'])

for i in range(len(pairA)):
    # fetching liquidity pool
    if (stellar_sdk.LiquidityPoolAsset.is_valid_lexicographic_order(pairA[i], pairB[i])):
        liqpool = stellar_sdk.LiquidityPoolAsset(pairA[i], pairB[i], stellar_sdk.LIQUIDITY_POOL_FEE_V18)
    elif (stellar_sdk.LiquidityPoolAsset.is_valid_lexicographic_order(pairA[i], pairB[i]) == False):
        liqpool = stellar_sdk.LiquidityPoolAsset(pairB[i], pairA[i], stellar_sdk.LIQUIDITY_POOL_FEE_V18)
    liqpool_id = liqpool.liquidity_pool_id
    try:
        response = requests.get('https://horizon.stellar.org/liquidity_pools/' + liqpool_id)
        liqpool_details = response.json()
    except:
        no_liqpool=True
    # fetching orderbook details
    ob_details = serverpublic.orderbook(pairA[i], pairB[i]).limit(98).call()
    ob_details2 = serverpublic.orderbook(pairB[i], pairA[i]).limit(98).call()
    pairA[i]=Asset(pairA[i].code, issuer_acc.public_key)
    pairB[i]=Asset(pairB[i].code, issuer_acc.public_key)

    if (stellar_sdk.LiquidityPoolAsset.is_valid_lexicographic_order(pairA[i], pairB[i])):
        liqpool_testnet = stellar_sdk.LiquidityPoolAsset(pairA[i], pairB[i], stellar_sdk.LIQUIDITY_POOL_FEE_V18)
    elif (stellar_sdk.LiquidityPoolAsset.is_valid_lexicographic_order(pairA[i], pairB[i]) == False):
        liqpool_details['reserves'][0]['amount'], liqpool_details['reserves'][1]['amount'] = \
            liqpool_details['reserves'][1]['amount'], liqpool_details['reserves'][0]['amount']
        liqpool_testnet = stellar_sdk.LiquidityPoolAsset(pairB[i], pairA[i], stellar_sdk.LIQUIDITY_POOL_FEE_V18)
    liqpool_id_testnet = liqpool_testnet.liquidity_pool_id

    mm1_acc_loaded = server.load_account(marketmaker1_acc.public_key)

    MarketMaking1=TransactionBuilder(
        source_account=mm1_acc_loaded,
        network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
        base_fee=base_fee,
    )
    liqpool_exist = False
    try:
        liqpool_details['status']==404
    except:
        liqpool_exist=True
    if liqpool_exist==True :
        if(float(liqpool_details['reserves'][0]['amount']) != 0):
            MarketMaking1.append_change_trust_liquidity_pool_asset_op(
                asset=liqpool_testnet
            )
            MarketMaking1.append_liquidity_pool_deposit_op(
                max_amount_a=liqpool_details['reserves'][0]['amount'],
                max_amount_b=liqpool_details['reserves'][1]['amount'],
                max_price='100000000',
                min_price='0.0000001',
                liquidity_pool_id=liqpool_id_testnet
            )
    for x in range(len(ob_details['asks'])):
        MarketMaking1.append_manage_sell_offer_op(
            selling_code=pairA[i].code,
            selling_issuer=pairA[i].issuer,
            buying_code=pairB[i].code,
            buying_issuer=pairB[i].issuer,
            amount=ob_details['asks'][x]['amount'],
            price=ob_details['asks'][x]['price']
        )
    MarketMaking1=MarketMaking1.build()
    MarketMaking1.sign(marketmaker1_acc.secret)
    try:
        response = server.submit_transaction(MarketMaking1)
        print('TxHash = ' + response['hash'])
    except :
        print('No Sell Order And Liquidity Pool Found')
    finally:
        mm2_acc_loaded = server.load_account(marketmaker2_acc.public_key)

        MarketMaking2 = TransactionBuilder(
            source_account=mm2_acc_loaded,
            network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
            base_fee=base_fee,
        )
        for x in range(len(ob_details2['asks'])):
            #print(ob_details2['asks'][x])
            MarketMaking2.append_manage_sell_offer_op(
                selling_code=pairB[i].code,
                selling_issuer=pairB[i].issuer,
                buying_code=pairA[i].code,
                buying_issuer=pairA[i].issuer,
                amount=ob_details2['asks'][x]['amount'],
                price=ob_details2['asks'][x]['price']
            )
        MarketMaking2=MarketMaking2.build()
        MarketMaking2.sign(marketmaker2_acc.secret)
        try:
            response=server.submit_transaction(MarketMaking2)
            print('TxHash = ' + response['hash'])
        except:
            print('No Buy Order Found')
        print('pair ' + pairA[i].code+'-'+pairB[i].code + ' Successfully Replicated')
