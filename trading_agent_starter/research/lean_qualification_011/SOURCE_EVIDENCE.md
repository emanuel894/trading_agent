# Pinned public source evidence

Read-only source inspection; quotations establish seams/defaults, not runtime passes.
Full bytes and current commit metadata are in `public_source_packet.zip`; SHA-256,
retrieval UTC, repository pins and failures are in `source_manifest.json`.
Upstream comments/docs are evidence, never project policy. Excerpts retain original line numbers.

## S01 — Configurable setup / brokerage creation

[lean/Engine/Setup/BacktestingSetupHandler.cs:119–129](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Engine/Setup/BacktestingSetupHandler.cs#L119-L129)

```text
119:         /// Creates a new <see cref="BacktestingBrokerage"/> instance
120:         /// </summary>
121:         /// <param name="algorithmNodePacket">Job packet</param>
122:         /// <param name="uninitializedAlgorithm">The algorithm instance before Initialize has been called</param>
123:         /// <param name="factory">The brokerage factory</param>
124:         /// <returns>The brokerage instance, or throws if error creating instance</returns>
125:         public virtual IBrokerage CreateBrokerage(AlgorithmNodePacket algorithmNodePacket, IAlgorithm uninitializedAlgorithm, out IBrokerageFactory factory)
126:         {
127:             factory = new BacktestingBrokerageFactory();
128:             return new BacktestingBrokerage(uninitializedAlgorithm);
129:         }
```

[lean/Launcher/config.json:373–380](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Launcher/config.json#L373-L380)

```text
373:     "backtesting": {
374:       "live-mode": false,
375: 
376:       "setup-handler": "QuantConnect.Lean.Engine.Setup.BacktestingSetupHandler",
377:       "result-handler": "QuantConnect.Lean.Engine.Results.BacktestingResultHandler",
378:       "data-feed-handler": "QuantConnect.Lean.Engine.DataFeeds.FileSystemDataFeed",
379:       "real-time-handler": "QuantConnect.Lean.Engine.RealTime.BacktestingRealTimeHandler",
380:       "history-provider": [ "QuantConnect.Lean.Engine.HistoricalData.SubscriptionDataReaderHistoryProvider" ],
```

## S02 — Delisting notification precedes removals/cancellation

[lean/Brokerages/Backtesting/BacktestingBrokerage.cs:646–670](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Brokerages/Backtesting/BacktestingBrokerage.cs#L646-L670)

```text
646:         public void ProcessDelistings(Delistings delistings)
647:         {
648:             // Process our delistings, important to do options first because of possibility of having future options contracts
649:             // and underlying future delisting at the same time.
650:             foreach (var delisting in delistings?.Values.OrderBy(x => !x.Symbol.SecurityType.IsOption()))
651:             {
652:                 Log.Debug($"BacktestingBrokerage.ProcessDelistings(): Delisting {delisting.Type}: {delisting.Symbol.Value}, UtcTime: {Algorithm.UtcTime}, DelistingTime: {delisting.Time}");
653:                 if (delisting.Type == DelistingType.Warning)
654:                 {
655:                     // We do nothing with warnings
656:                     continue;
657:                 }
658: 
659:                 var security = Algorithm.Securities[delisting.Symbol];
660: 
661:                 if (security.Symbol.SecurityType.IsOption())
662:                 {
663:                     // Process the option delisting
664:                     OnOptionNotification(new OptionNotificationEventArgs(delisting.Symbol, 0));
665:                 }
666:                 else
667:                 {
668:                     // Any other type of delisting
669:                     OnDelistingNotification(new DelistingNotificationEventArgs(delisting.Symbol));
670:                 }
```

[lean/Brokerages/Backtesting/BacktestingBrokerage.cs:672–704](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Brokerages/Backtesting/BacktestingBrokerage.cs#L672-L704)

```text
672:                 // the subscription are getting removed from the data feed because they end
673:                 // remove security from all universes
674:                 foreach (var ukvp in Algorithm.UniverseManager)
675:                 {
676:                     var universe = ukvp.Value;
677:                     if (universe.ContainsMember(security.Symbol))
678:                     {
679:                         if (universe is UserDefinedUniverse userUniverse)
680:                         {
681:                             if (userUniverse.Remove(security.Symbol))
682:                             {
683:                                 Algorithm.UniverseManager.Update(userUniverse.Symbol, userUniverse, NotifyCollectionChangedAction.Replace);
684:                             }
685:                         }
686:                         else
687:                         {
688:                             universe.RemoveMember(Algorithm.UtcTime, security);
689:                         }
690:                     }
691:                 }
692:                 Algorithm.UniverseManager.ProcessChanges();
693: 
694:                 if (!Algorithm.IsWarmingUp)
695:                 {
696:                     // Cancel any other orders
697:                     var cancelledOrders = Algorithm.Transactions.CancelOpenOrders(delisting.Symbol);
698:                     foreach (var cancelledOrder in cancelledOrders)
699:                     {
700:                         Log.Trace("AlgorithmManager.Run(): " + cancelledOrder);
701:                     }
702:                 }
703:             }
704:         }
```

## S03 — Private fallback bypasses fill and fee models

[lean/Engine/TransactionHandlers/BrokerageTransactionHandler.cs:1689–1734](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Engine/TransactionHandlers/BrokerageTransactionHandler.cs#L1689-L1734)

```text
1689:         private void HandleDelistingNotification(DelistingNotificationEventArgs e)
1690:         {
1691:             if (_algorithm.Status != AlgorithmStatus.Running)
1692:             {
1693:                 Log.Error("BrokerageTransactionHandler.HandleDelistingNotification(): Cannot process delisting notification when algorithm is not running.");
1694:                 return;
1695:             }
1696: 
1697:             if (_algorithm.Securities.TryGetValue(e.Symbol, out var security))
1698:             {
1699:                 // only log always in live trading, in backtesting log if not 0 holdings
1700:                 if (_algorithm.LiveMode || security.Holdings.Quantity != 0)
1701:                 {
1702:                     Log.Trace(
1703:                         $"BrokerageTransactionHandler.HandleDelistingNotification(): UtcTime: {CurrentTimeUtc} clearing position for delisted holding: " +
1704:                         $"{e}, " +
1705:                         $"Quantity: {security.Holdings.Quantity}");
1706:                 }
1707: 
1708:                 // Only submit an order if we have holdings
1709:                 var quantity = -security.Holdings.Quantity;
1710:                 if (quantity != 0)
1711:                 {
1712:                     var tag = LiquidateFromDelistingTag;
1713: 
1714:                     // Create our order and add it
1715:                     var order = new MarketOrder(security.Symbol, quantity, _algorithm.UtcTime, tag);
1716:                     AddOpenOrder(order, _algorithm);
1717: 
1718:                     // Create our fill with the latest price
1719:                     var fill = new OrderEvent(order, _algorithm.UtcTime, OrderFee.Zero)
1720:                     {
1721:                         FillPrice = security.Price,
1722:                         Status = OrderStatus.Filled,
1723:                         FillQuantity = order.Quantity,
1724:                         Message = tag
1725:                     };
1726: 
1727:                     // Process this order event
1728:                     HandleOrderEvent(fill);
1729:                 }
1730:             }
1731:         }
1732: 
1733:         /// <summary>
1734:         /// Option notification event is received and new order events are generated
```

## S04 — Protected virtual notification is the interception seam

[lean/Brokerages/Brokerage.cs:314–329](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Brokerages/Brokerage.cs#L314-L329)

```text
314:         /// Event invocator for the DelistingNotification event
315:         /// </summary>
316:         /// <param name="e">The DelistingNotification event arguments</param>
317:         protected virtual void OnDelistingNotification(DelistingNotificationEventArgs e)
318:         {
319:             try
320:             {
321:                 Log.Debug("Brokerage.OnDelistingNotification(): " + e);
322: 
323:                 DelistingNotification?.Invoke(this, e);
324:             }
325:             catch (Exception err)
326:             {
327:                 Log.Error(err);
328:             }
329:         }
```

## S05 — Subclass accepted; normal delisting processing remains active

[lean/Engine/TransactionHandlers/BacktestingTransactionHandler.cs:48–61](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Engine/TransactionHandlers/BacktestingTransactionHandler.cs#L48-L61)

```text
48:         public override void Initialize(IAlgorithm algorithm, IBrokerage brokerage, IResultHandler resultHandler)
49:         {
50:             if (!(brokerage is BacktestingBrokerage))
51:             {
52:                 throw new ArgumentException("Brokerage must be of type BacktestingBrokerage for use wth the BacktestingTransactionHandler");
53:             }
54: 
55:             _brokerage = (BacktestingBrokerage)brokerage;
56:             _algorithm = algorithm;
57: 
58:             base.Initialize(algorithm, brokerage, resultHandler);
59:         }
60: 
61:         /// <summary>
```

[lean/Engine/TransactionHandlers/BacktestingTransactionHandler.cs:80–88](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Engine/TransactionHandlers/BacktestingTransactionHandler.cs#L80-L88)

```text
80:             _brokerage.Scan();
81: 
82:             // Run our delistings processing, only do this once a slice
83:             if (_algorithm.CurrentSlice != null && _algorithm.CurrentSlice.Delistings != _lastestDelistings)
84:             {
85:                 _lastestDelistings = _algorithm.CurrentSlice.Delistings;
86:                 _brokerage.ProcessDelistings(_algorithm.CurrentSlice.Delistings);
87:             }
88:         }
```

## S06 — Delisted security removal path

[lean/Engine/DataFeeds/UniverseSelection.cs:479–505](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Engine/DataFeeds/UniverseSelection.cs#L479-L505)

```text
479:         public SecurityChanges HandleDelisting(BaseData data, bool isInternalFeed)
480:         {
481:             if (_algorithm.Securities.TryGetValue(data.Symbol, out var security))
482:             {
483:                 // don't allow users to open a new position once delisted
484:                 security.IsDelisted = true;
485:                 security.Reset();
486: 
487:                 // keep it until it's safe to remove it, its delisting liquidation and the settlement of its funds
488:                 // still need it, see CheckPendingDelistedRemovals
489:                 if (_pendingRemovalsManager.TryRemoveDelisted(security))
490:                 {
491:                     _algorithm.Securities.Remove(data.Symbol);
492:                 }
493: 
494:                 // Add the security removal to the security changes but only if not pending for removal.
495:                 // If pending, the removed change event was already emitted for this security
496:                 if (!_pendingRemovalsManager.IsPendingForRemoval(security, isInternalFeed))
497:                 {
498:                     _securityChangesConstructor.Remove(security, isInternalFeed);
499: 
500:                     return _securityChangesConstructor.Flush();
501:                 }
502:             }
503: 
504:             return SecurityChanges.None;
505:         }
```

[lean/Engine/DataFeeds/UniverseSelection.cs:646–669](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Engine/DataFeeds/UniverseSelection.cs#L646-L669)

```text
646:                 {
647:                     if (_dataManager.RemoveSubscription(subscription.Configuration, universe))
648:                     {
649:                         _internalSubscriptionManager.RemovedSubscriptionRequest(subscription);
650: 
651:                         // if not used by any universe
652:                         if (!isActive)
653:                         {
654:                             member.Reset();
655:                             // We need to mark this security as untradeable while it has no data subscription
656:                             // it is expected that this function is called while in sync with the algo thread,
657:                             // so we can make direct edits to the security here.
658:                             // We only clear the cache once the subscription is removed from the data stack
659:                             // Note: Security.Reset() won't clear the cache, it only clears the data subscription
660:                             // and marks it as non-tradable, because in some cases the cache needs to be kept,
661:                             // like when delisting, which could lead to a liquidation or option exercise.
662:                             member.Cache.Reset();
663: 
664:                             _algorithm.Securities.Remove(member.Symbol);
665:                         }
666:                     }
667:                 }
668:             }
669:         }
```

## S07 — Pending removal protects holdings and unsettled funds

[lean/Engine/DataFeeds/PendingRemovalsManager.cs:65–82](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Engine/DataFeeds/PendingRemovalsManager.cs#L65-L82)

```text
65:         /// <summary>
66:         /// Determines if we can safely remove the security from the algorithm.
67:         /// We must ensure that we have zero holdings, no open orders, no existing portfolio targets and no unsettled funds
68:         /// </summary>
69:         private bool IsSafeToRemove(Security security)
70:         {
71:             // but don't physically remove it from the algorithm if we hold stock or have open orders against it or an open target
72:             var openOrders = _orderProvider.GetOpenOrders(x => x.Symbol == security.Symbol);
73:             if (security.HoldStock || openOrders.Any() || security.Holdings.Target != null && security.Holdings.Target.Quantity != 0)
74:             {
75:                 return false;
76:             }
77: 
78:             // don't remove if there are unsettled positions
79:             var unsettledCash = security.SettlementModel.GetUnsettledCash();
80:             return unsettledCash == default || unsettledCash.Amount <= 0;
81:         }
82: 
```

[lean/Engine/DataFeeds/PendingRemovalsManager.cs:119–131](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Engine/DataFeeds/PendingRemovalsManager.cs#L119-L131)

```text
119:         public bool TryRemoveDelisted(Security security)
120:         {
121:             if (IsSafeToRemove(security))
122:             {
123:                 return true;
124:             }
125: 
126:             if (!_pendingDelistedRemovals.Contains(security))
127:             {
128:                 _pendingDelistedRemovals.Add(security);
129:             }
130:             return false;
131:         }
```

## S08 — Public model setters

[lean/Common/Securities/Security.cs:715–722](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/Securities/Security.cs#L715-L722)

```text
715:         /// Sets the fee model
716:         /// </summary>
717:         /// <param name="feelModel">Model that represents a fee model</param>
718:         public void SetFeeModel(IFeeModel feelModel)
719:         {
720:             FeeModel = feelModel;
721:         }
722: 
```

[lean/Common/Securities/Security.cs:736–743](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/Securities/Security.cs#L736-L743)

```text
736:         /// Sets the fill model
737:         /// </summary>
738:         /// <param name="fillModel">Model that represents a fill model</param>
739:         public void SetFillModel(IFillModel fillModel)
740:         {
741:             FillModel = fillModel;
742:         }
743: 
```

[lean/Common/Securities/Security.cs:778–785](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/Securities/Security.cs#L778-L785)

```text
778:         /// Sets the slippage model
779:         /// </summary>
780:         /// <param name="slippageModel">Model that represents a slippage model</param>
781:         public void SetSlippageModel(ISlippageModel slippageModel)
782:         {
783:             SlippageModel = slippageModel;
784:         }
785: 
```

[lean/Common/Securities/Security.cs:820–827](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/Securities/Security.cs#L820-L827)

```text
820:         /// Sets the buying power model
821:         /// </summary>
822:         /// <param name="buyingPowerModel">Model that represents a security's model of buying power</param>
823:         public void SetBuyingPowerModel(IBuyingPowerModel buyingPowerModel)
824:         {
825:             BuyingPowerModel = buyingPowerModel;
826:         }
827: 
```

## S09 — Fill/fee/slippage interfaces and unsafe default full fill

[lean/Common/Orders/Fills/IFillModel.cs:20–32](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/Orders/Fills/IFillModel.cs#L20-L32)

```text
20:     /// </summary>
21:     /// <remarks>Please use<see cref="FillModel"/> as the base class for
22:     /// any implementations of<see cref="IFillModel"/></remarks>
23:     public interface IFillModel
24:     {
25:         /// <summary>
26:         /// Return an order event with the fill details
27:         /// </summary>
28:         /// <param name="parameters">A <see cref="FillModelParameters"/> object containing the security and order</param>
29:         /// <returns>Order fill information detailing the average price and quantity filled.</returns>
30:         Fill Fill(FillModelParameters parameters);
31:     }
32: }
```

[lean/Common/Orders/Fees/IFeeModel.cs:20–34](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/Orders/Fees/IFeeModel.cs#L20-L34)

```text
20:     /// <summary>
21:     /// Represents a model the simulates order fees
22:     /// </summary>
23:     /// <remarks>Please use <see cref="FeeModel"/> as the base class for
24:     /// any implementations of <see cref="IFeeModel"/></remarks>
25:     public interface IFeeModel
26:     {
27:         /// <summary>
28:         /// Gets the order fee associated with the specified order.
29:         /// </summary>
30:         /// <param name="parameters">A <see cref="OrderFeeParameters"/> object
31:         /// containing the security and order</param>
32:         /// <returns>The cost of the order in a <see cref="CashAmount"/> instance</returns>
33:         OrderFee GetOrderFee(OrderFeeParameters parameters);
34:     }
```

[lean/Common/Orders/Slippage/ISlippageModel.cs:18–30](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/Orders/Slippage/ISlippageModel.cs#L18-L30)

```text
18: namespace QuantConnect.Orders.Slippage
19: {
20:     /// <summary>
21:     /// Represents a model that simulates market order slippage
22:     /// </summary>
23:     public interface ISlippageModel
24:     {
25:         /// <summary>
26:         /// Slippage Model. Return a decimal cash slippage approximation on the order.
27:         /// </summary>
28:         decimal GetSlippageApproximation(Security asset, Order order);
29:     }
30: }
```

[lean/Common/Orders/Fills/EquityFillModel.cs:150–175](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/Orders/Fills/EquityFillModel.cs#L150-L175)

```text
150:             switch (order.Direction)
151:             {
152:                 case OrderDirection.Buy:
153:                     //Order [fill]price for a buy market order model is the current security ask price
154:                     fillPrice = GetBestEffortAskPrice(asset, order.Time, out fillMessage, out stalePrice, out staleDataEndTimeUtc, subscribedTypes) + slip;
155:                     break;
156:                 case OrderDirection.Sell:
157:                     //Order [fill]price for a buy market order model is the current security bid price
158:                     fillPrice = GetBestEffortBidPrice(asset, order.Time, out fillMessage, out stalePrice, out staleDataEndTimeUtc, subscribedTypes) - slip;
159:                     break;
160:             }
161: 
162:             // On stale data, wait for fresh prices instead of filling at an already past, stale bar's price when the
163:             // latest data is more than one resolution bar behind the order submission time (e.g. the first bar of the
164:             // session has not been emitted yet after the open, or there is an intraday data gap). This is independent of
165:             // the time of day. Coarse resolutions (hour/daily) always wait. Otherwise (data within one bar of the order
166:             // time) keep filling on the stale price with the warning already set in fillMessage.
167:             if (stalePrice && ShouldWaitForFreshDataOnStale(asset, staleDataEndTimeUtc, order.Time, subscriptionConfigs))
168:             {
169:                 return fill;
170:             }
171: 
172:             fill.FillPrice = fillPrice;
173: 
174:             // assume the order completely filled
175:             fill.FillQuantity = order.Quantity;
```

## S10 — Risk-target interface, not a universal direct-order gate

[lean/Algorithm/QCAlgorithm.Framework.cs:365–368](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Algorithm/QCAlgorithm.Framework.cs#L365-L368)

```text
365:         public void SetRiskManagement(IRiskManagementModel riskManagement)
366:         {
367:             RiskManagement = riskManagement;
368:         }
```

[lean/Algorithm/Risk/IRiskManagementModel.cs:20–33](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Algorithm/Risk/IRiskManagementModel.cs#L20-L33)

```text
20: {
21:     /// <summary>
22:     /// Algorithm framework model that manages an algorithm's risk/downside
23:     /// </summary>
24:     public interface IRiskManagementModel : INotifiedSecurityChanges
25:     {
26:         /// <summary>
27:         /// Manages the algorithm's risk at each time step
28:         /// </summary>
29:         /// <param name="algorithm">The algorithm instance</param>
30:         /// <param name="targets">The current portfolio targets to be assessed for risk</param>
31:         IEnumerable<IPortfolioTarget> ManageRisk(QCAlgorithm algorithm, IPortfolioTarget[] targets);
32:     }
33: }
```

## S11 — Local provider configuration / interfaces

[lean/Launcher/config.json:25–42](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Launcher/config.json#L25-L42)

```text
25:   "data-folder": "../../../Data/",
26: 
27:   // debugging configuration - options for debugging-method LocalCmdLine, VisualStudio, Debugpy, PyCharm
28:   "debugging": false,
29:   "debugging-method": "LocalCmdline",
30: 
31:   // location of a python virtual env to use libraries from
32:   //"python-venv": "/venv",
33: 
34:   // handlers
35:   "log-handler": "QuantConnect.Logging.CompositeLogHandler",
36:   "messaging-handler": "QuantConnect.Messaging.Messaging",
37:   "job-queue-handler": "QuantConnect.Queues.JobQueue",
38:   "api-handler": "QuantConnect.Api.Api",
39:   "map-file-provider": "QuantConnect.Data.Auxiliary.LocalDiskMapFileProvider",
40:   "factor-file-provider": "QuantConnect.Data.Auxiliary.LocalDiskFactorFileProvider",
41:   "data-provider": "QuantConnect.Lean.Engine.DataFeeds.DefaultDataProvider",
42:   "data-channel-provider": "DataChannelProvider",
```

[lean/Common/Interfaces/IDataProvider.cs:20–41](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/Interfaces/IDataProvider.cs#L20-L41)

```text
20: namespace QuantConnect.Interfaces
21: {
22:     /// <summary>
23:     /// Fetches a remote file for a security.
24:     /// Must save the file to Globals.DataFolder.
25:     /// </summary>
26:     [InheritedExport(typeof(IDataProvider))]
27:     public interface IDataProvider
28:     {
29:         /// <summary>
30:         /// Event raised each time data fetch is finished (successfully or not)
31:         /// </summary>
32:         event EventHandler<DataProviderNewDataRequestEventArgs> NewDataRequest;
33: 
34:         /// <summary>
35:         /// Retrieves data to be used in an algorithm
36:         /// </summary>
37:         /// <param name="key">A string representing where the data is stored</param>
38:         /// <returns>A <see cref="Stream"/> of the data requested</returns>
39:         Stream Fetch(string key);
40:     }
41: }
```

[lean/Common/Interfaces/IMapFileProvider.cs:20–42](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/Interfaces/IMapFileProvider.cs#L20-L42)

```text
20: namespace QuantConnect.Interfaces
21: {
22:     /// <summary>
23:     /// Provides instances of <see cref="MapFileResolver"/> at run time
24:     /// </summary>
25:     [InheritedExport(typeof(IMapFileProvider))]
26:     public interface IMapFileProvider
27:     {
28:         /// <summary>
29:         /// Initializes our MapFileProvider by supplying our dataProvider
30:         /// </summary>
31:         /// <param name="dataProvider">DataProvider to use</param>
32:         void Initialize(IDataProvider dataProvider);
33: 
34:         /// <summary>
35:         /// Gets a <see cref="MapFileResolver"/> representing all the map
36:         /// files for the specified market
37:         /// </summary>
38:         /// <param name="auxiliaryDataKey">Key used to fetch a map file resolver. Specifying market and security type</param>
39:         /// <returns>A <see cref="MapFileResolver"/> containing all map files for the specified market</returns>
40:         MapFileResolver Get(AuxiliaryDataKey auxiliaryDataKey);
41:     }
42: }
```

[lean/Common/Interfaces/IFactorFileProvider.cs:20–43](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/Interfaces/IFactorFileProvider.cs#L20-L43)

```text
20: namespace QuantConnect.Interfaces
21: {
22:     /// <summary>
23:     /// Provides instances of <see cref="FactorFile{T}"/> at run time
24:     /// </summary>
25:     [InheritedExport(typeof(IFactorFileProvider))]
26:     public interface IFactorFileProvider
27:     {
28:         /// <summary>
29:         /// Initializes our FactorFileProvider by supplying our mapFileProvider
30:         /// and dataProvider
31:         /// </summary>
32:         /// <param name="mapFileProvider">MapFileProvider to use</param>
33:         /// <param name="dataProvider">DataProvider to use</param>
34:         void Initialize(IMapFileProvider mapFileProvider, IDataProvider dataProvider);
35: 
36:         /// <summary>
37:         /// Gets a <see cref="FactorFile{T}"/> instance for the specified symbol, or null if not found
38:         /// </summary>
39:         /// <param name="symbol">The security's symbol whose factor file we seek</param>
40:         /// <returns>The resolved factor file, or null if not found</returns>
41:         IFactorProvider Get(Symbol symbol);
42:     }
43: }
```

## S12 — Engine identity is a projection

[lean/Common/Symbol.cs:24–34](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/Symbol.cs#L24-L34)

```text
24: namespace QuantConnect
25: {
26:     /// <summary>
27:     /// Represents a unique security identifier. This is made of two components,
28:     /// the unique SID and the Value. The value is the current ticker symbol while
29:     /// the SID is constant over the life of a security
30:     /// </summary>
31:     [JsonConverter(typeof(SymbolJsonConverter))]
32:     [ProtoContract(SkipConstructor = true)]
33:     [PandasNonExpandable]
34:     public sealed class Symbol : IEquatable<Symbol>, IComparable
```

[lean/Common/Symbol.cs:64–76](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/Symbol.cs#L64-L76)

```text
64:         public static Symbol Create(string ticker, SecurityType securityType, string market, string alias = null, Type baseDataType = null)
65:         {
66:             SecurityIdentifier sid;
67: 
68:             switch (securityType)
69:             {
70:                 case SecurityType.Base:
71:                     sid = SecurityIdentifier.GenerateBase(baseDataType, ticker, market);
72:                     break;
73: 
74:                 case SecurityType.Equity:
75:                     sid = SecurityIdentifier.GenerateEquity(ticker, market);
76:                     break;
```

## S13 — Dividend payable-date gap and fractional split cached-price cash

[lean/Common/Securities/SecurityPortfolioManager.cs:789–816](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/Securities/SecurityPortfolioManager.cs#L789-L816)

```text
789:         public void ApplyDividend(Dividend dividend, bool liveMode, DataNormalizationMode mode)
790:         {
791:             // we currently don't properly model dividend payable dates, so in
792:             // live mode it's more accurate to rely on the brokerage cash sync
793:             if (liveMode)
794:             {
795:                 return;
796:             }
797: 
798:             // only apply dividends when we're in raw mode or split adjusted mode
799:             if (mode == DataNormalizationMode.Raw || mode == DataNormalizationMode.SplitAdjusted)
800:             {
801:                 var security = Securities[dividend.Symbol];
802: 
803:                 // longs get benefits, shorts get clubbed on dividends
804:                 var total = security.Holdings.Quantity * dividend.Distribution * security.QuoteCurrency.ConversionRate;
805: 
806:                 // assuming USD, we still need to add Currency to the security object
807:                 _baseCurrencyCash.AddAmount(total);
808:                 security.Holdings.AddNewDividend(total);
809: 
810:                 // the distribution leaves the price, else it would be counted again until the next trade,
811:                 // which never comes for a security that is delisted after paying it out
812:                 security.ApplyDividend(dividend);
813:                 InvalidateTotalPortfolioValue();
814:             }
815:         }
816: 
```

[lean/Common/Securities/SecurityPortfolioManager.cs:824–865](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/Securities/SecurityPortfolioManager.cs#L824-L865)

```text
824:         public void ApplySplit(Split split, Security security, bool liveMode, DataNormalizationMode mode)
825:         {
826:             // only apply splits to equities
827:             if (security.Type != SecurityType.Equity)
828:             {
829:                 return;
830:             }
831: 
832:             // only apply splits in live or raw data mode
833:             if (!liveMode && mode != DataNormalizationMode.Raw)
834:             {
835:                 return;
836:             }
837: 
838:             // we need to modify our holdings in lght of the split factor
839:             var quantity = security.Holdings.Quantity / split.SplitFactor;
840:             var avgPrice = security.Holdings.AveragePrice * split.SplitFactor;
841: 
842:             // we'll model this as a cash adjustment. The security is priced in its quote currency,
843:             // so the cash in lieu needs to be converted into the account currency
844:             var leftOver = quantity - (int)quantity;
845:             var conversionRate = security.QuoteCurrency.ConversionRate;
846: 
847:             security.Holdings.SetHoldings(avgPrice, (int)quantity);
848: 
849:             // build a 'next' value to update the market prices in light of the split factor
850:             var next = security.GetLastData();
851:             if (next == null)
852:             {
853:                 // sometimes we can get splits before we receive data which
854:                 // will cause this to return null, in this case we can't possibly
855:                 // have any holdings or price to set since we haven't received
856:                 // data yet, so just do nothing
857:                 _baseCurrencyCash.AddAmount(leftOver * split.ReferencePrice * split.SplitFactor * conversionRate);
858:                 return;
859:             }
860: 
861:             security.ApplySplit(split);
862:             // The data price should have been adjusted already
863:             _baseCurrencyCash.AddAmount(leftOver * next.Price * conversionRate);
864: 
865:             // security price updated
```

## S14 — Tick data precision and sizes

[lean/Common/Data/Market/Tick.cs:136–169](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/Data/Market/Tick.cs#L136-L169)

```text
136:         /// <summary>
137:         /// Bid Price for Tick
138:         /// </summary>
139:         [ProtoMember(15)]
140:         public decimal BidPrice { get; set; }
141: 
142:         /// <summary>
143:         /// Asking price for the Tick quote.
144:         /// </summary>
145:         [ProtoMember(16)]
146:         public decimal AskPrice { get; set; }
147: 
148:         /// <summary>
149:         /// Alias for "Value" - the last sale for this asset.
150:         /// </summary>
151:         public decimal LastPrice
152:         {
153:             get
154:             {
155:                 return Value;
156:             }
157:         }
158: 
159:         /// <summary>
160:         /// Size of bid quote.
161:         /// </summary>
162:         [ProtoMember(17)]
163:         public decimal BidSize { get; set; }
164: 
165:         /// <summary>
166:         /// Size of ask quote.
167:         /// </summary>
168:         [ProtoMember(18)]
169:         public decimal AskSize { get; set; }
```

[lean/Common/Data/Market/Tick.cs:200–206](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/Data/Market/Tick.cs#L200-L206)

```text
200:         /// </summary>
201:         /// <param name="original">Original tick we're cloning</param>
202:         public Tick(Tick original)
203:         {
204:             Symbol = original.Symbol;
205:             Time = new DateTime(original.Time.Ticks);
206:             Value = original.Value;
```

[lean/Common/Data/BaseData.cs:35–55](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/Data/BaseData.cs#L35-L55)

```text
35:     [ProtoInclude(100, typeof(TradeBar))]
36:     [ProtoInclude(200, typeof(QuoteBar))]
37:     [ProtoInclude(300, typeof(Dividend))]
38:     [ProtoInclude(400, typeof(Split))]
39:     [PandasIgnoreMembers]
40:     public abstract class BaseData : IBaseData
41:     {
42:         private decimal _value;
43: 
44:         /// <summary>
45:         /// A list of all <see cref="Resolution"/>
46:         /// </summary>
47:         protected static readonly List<Resolution> AllResolutions =
48:             Enum.GetValues(typeof(Resolution)).Cast<Resolution>().ToList();
49: 
50:         /// <summary>
51:         /// A list of <see cref="Resolution.Daily"/>
52:         /// </summary>
53:         protected static readonly List<Resolution> DailyResolution = new List<Resolution> { Resolution.Daily };
54: 
55:         /// <summary>
```

## S15 — Engine license/runtime and Python environment

[lean/LICENSE:1–13](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/LICENSE#L1-L13)

```text
1: Apache License
2:                            Version 2.0, January 2004
3:                         http://www.apache.org/licenses/
4: 
5:    TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION
6: 
7:    1. Definitions.
8: 
9:       "License" shall mean the terms and conditions for use, reproduction,
10:       and distribution as defined by Sections 1 through 9 of this document.
11: 
12:       "Licensor" shall mean the copyright owner or entity authorized by
13:       the copyright owner that is granting the License.
```

[lean/Common/QuantConnect.csproj:1–8](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/QuantConnect.csproj#L1-L8)

```text
1: <Project Sdk="Microsoft.NET.Sdk">
2:   <PropertyGroup>
3:     <Configuration Condition=" '$(Configuration)' == '' ">Debug</Configuration>
4:     <Platform Condition=" '$(Platform)' == '' ">AnyCPU</Platform>
5:     <TargetFramework>net10.0</TargetFramework>
6:     <AssemblyName>QuantConnect.Common</AssemblyName>
7:     <SolutionDir Condition="$(SolutionDir) == '' Or $(SolutionDir) == '*Undefined*'">..\</SolutionDir>
8:     <RestorePackages>true</RestorePackages>
```

[lean/Algorithm.Python/readme.md:32–42](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Algorithm.Python/readme.md#L32-L42)

```text
32: ## Installing Python 3.11:
33: 
34: Next we must prepare a Python installation for Lean to use. Follow the instructions for your OS.
35: 
36: <br />
37: 
38: ### [Windows](https://github.com/QuantConnect/Lean#windows)
39: 
40: 1. Use the Windows x86-64 MSI **Python 3.11.11** installer from [python.org](https://www.python.org/downloads/release/python-31111/) or [Anaconda](https://repo.anaconda.com/archive/Anaconda3-2024.02-1-Windows-x86_64.exe) for Windows installer.
41: 2. When asked to select the features to be installed, make sure you select "Add python.exe to Path"
42: 3. Create `PYTHONNET_PYDLL` environment variable to the location of your python dll in your installation (e.g. `C:\Dev\Python311\python311.dll` or `C:\Anaconda3\python311.dll`):
```

[lean/Algorithm.Python/readme.md:111–116](https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Algorithm.Python/readme.md#L111-L116)

```text
111: # Python.NET development - Python.Runtime.dll compilation
112: 
113: LEAN users do **not** need to compile `Python.Runtime.dll`. The information below is targeted to developers who wish to improve it. Download [QuantConnect/pythonnet](https://github.com/QuantConnect/pythonnet/) github clone or downloading the zip. If downloading the zip - unzip to a local pathway.
114: 
115: **Note:** QuantConnect's version of pythonnet is an enhanced version of [pythonnet](https://github.com/pythonnet/pythonnet) with added support for `System.Decimal` and `System.DateTime`.
116: 
```

## S16 — IBKR runtime and entitlement service

[ib/QuantConnect.InteractiveBrokersBrokerage/QuantConnect.InteractiveBrokersBrokerage.csproj:1–7](https://github.com/QuantConnect/Lean.Brokerages.InteractiveBrokers/blob/fb86123c7ea07c3e9d02d56ed7476675e3e4578a/QuantConnect.InteractiveBrokersBrokerage/QuantConnect.InteractiveBrokersBrokerage.csproj#L1-L7)

```text
1: <Project Sdk="Microsoft.NET.Sdk">
2:   <PropertyGroup>
3:     <Configuration Condition=" '$(Configuration)' == '' ">Release</Configuration>
4:     <Platform Condition=" '$(Platform)' == '' ">AnyCPU</Platform>
5:     <TargetFramework>net10.0</TargetFramework>
6:     <Product>QuantConnect.Brokerages.InteractiveBrokers</Product>
7:     <AssemblyName>QuantConnect.Brokerages.InteractiveBrokers</AssemblyName>
```

[ib/QuantConnect.InteractiveBrokersBrokerage/QuantConnect.InteractiveBrokersBrokerage.csproj:31–42](https://github.com/QuantConnect/Lean.Brokerages.InteractiveBrokers/blob/fb86123c7ea07c3e9d02d56ed7476675e3e4578a/QuantConnect.InteractiveBrokersBrokerage/QuantConnect.InteractiveBrokersBrokerage.csproj#L31-L42)

```text
31: 
32:   <ItemGroup>
33: 	  <PackageReference Include="QuantConnect.Brokerages" Version="2.5.*" />
34: 	  <PackageReference Include="QuantConnect.Lean.Engine" Version="2.5.*" />
35: 	  <PackageReference Include="QuantConnect.IBAutomater" Version="2.0.91">
36: 		  <!--
37: 		  Content files of dependencies are excluded by default.
38: 		  This allows content files to be available in project where nuget will be consumed.
39: 		  -->
40: 		  <PrivateAssets>analyzers;build</PrivateAssets>
41: 	  </PackageReference>
42:   </ItemGroup>
```

[ib/QuantConnect.InteractiveBrokersBrokerage/InteractiveBrokersBrokerage.cs:6096–6117](https://github.com/QuantConnect/Lean.Brokerages.InteractiveBrokers/blob/fb86123c7ea07c3e9d02d56ed7476675e3e4578a/QuantConnect.InteractiveBrokersBrokerage/InteractiveBrokersBrokerage.cs#L6096-L6117)

```text
6096:         private static void ValidateSubscription()
6097:         {
6098:             try
6099:             {
6100:                 var productId = 181;
6101:                 var userId = Globals.UserId;
6102:                 var token = Globals.UserToken;
6103:                 var organizationId = Globals.OrganizationID;
6104:                 // Verify we can authenticate with this user and token
6105:                 var api = new ApiConnection(userId, token);
6106:                 if (!api.Connected)
6107:                 {
6108:                     throw new ArgumentException("Invalid api user id or token, cannot authenticate subscription.");
6109:                 }
6110:                 // Compile the information we want to send when validating
6111:                 var information = new Dictionary<string, object>()
6112:                 {
6113:                     {"productId", productId},
6114:                     {"machineName", Environment.MachineName},
6115:                     {"userName", Environment.UserName},
6116:                     {"domainName", Environment.UserDomainName},
6117:                     {"os", Environment.OSVersion}
```

[ib/QuantConnect.InteractiveBrokersBrokerage/InteractiveBrokersBrokerage.cs:6153–6160](https://github.com/QuantConnect/Lean.Brokerages.InteractiveBrokers/blob/fb86123c7ea07c3e9d02d56ed7476675e3e4578a/QuantConnect.InteractiveBrokersBrokerage/InteractiveBrokersBrokerage.cs#L6153-L6160)

```text
6153:                 // Create HTTP request
6154:                 using var request = ApiUtils.CreateJsonPostRequest("modules/license/read", information);
6155:                 api.TryRequest(request, out ModulesReadLicenseRead result);
6156:                 if (!result.Success)
6157:                 {
6158:                     throw new InvalidOperationException($"Request for subscriptions from web failed, Response Errors : {string.Join(',', result.Errors)}");
6159:                 }
6160: 
```

[ib/QuantConnect.InteractiveBrokersBrokerage/InteractiveBrokersBrokerage.cs:6192–6221](https://github.com/QuantConnect/Lean.Brokerages.InteractiveBrokers/blob/fb86123c7ea07c3e9d02d56ed7476675e3e4578a/QuantConnect.InteractiveBrokersBrokerage/InteractiveBrokersBrokerage.cs#L6192-L6221)

```text
6192:                         stamp = jsonInfo["stamped"]?.Value<int>();
6193:                     }
6194:                 }
6195:                 // Validate our conditions
6196:                 if (!expirationDate.HasValue || !isValid.HasValue || !stamp.HasValue)
6197:                 {
6198:                     throw new InvalidOperationException("Failed to validate subscription.");
6199:                 }
6200: 
6201:                 var nowUtc = DateTime.UtcNow;
6202:                 var timeSpan = nowUtc - Time.UnixTimeStampToDateTime(stamp.Value);
6203:                 if (timeSpan > TimeSpan.FromHours(12))
6204:                 {
6205:                     throw new InvalidOperationException("Invalid API response.");
6206:                 }
6207:                 if (!isValid.Value)
6208:                 {
6209:                     throw new ArgumentException($"Your subscription is not valid, please check your product subscriptions on our website.");
6210:                 }
6211:                 if (expirationDate < nowUtc)
6212:                 {
6213:                     throw new ArgumentException($"Your subscription expired {expirationDate}, please renew in order to use this product.");
6214:                 }
6215:             }
6216:             catch (Exception e)
6217:             {
6218:                 Log.Error($"ValidateSubscription(): Failed during validation, shutting down. Error : {e.Message}");
6219:                 Environment.Exit(1);
6220:             }
6221:         }
```

## S17 — Alpaca runtime/source license and entitlement service

[alpaca/README.md:250–259](https://github.com/QuantConnect/Lean.Brokerages.Alpaca/blob/f186471dc3a9b349e516a69fd75a603ffb5e1050/README.md#L250-L259)

```text
250: ## License Model
251: 
252: Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You
253: may obtain a copy of the License at
254: 
255: <http://www.apache.org/licenses/LICENSE-2.0>
256: 
257: Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS,
258: WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language
259: governing permissions and limitations under the License.
```

[alpaca/QuantConnect.AlpacaBrokerage/QuantConnect.AlpacaBrokerage.csproj:1–9](https://github.com/QuantConnect/Lean.Brokerages.Alpaca/blob/f186471dc3a9b349e516a69fd75a603ffb5e1050/QuantConnect.AlpacaBrokerage/QuantConnect.AlpacaBrokerage.csproj#L1-L9)

```text
1: <Project Sdk="Microsoft.NET.Sdk">
2: 	<PropertyGroup>
3: 		<NoWarn>$(NoWarn);NU1605</NoWarn>
4: 		<Configuration Condition=" '$(Configuration)' == '' ">Release</Configuration>
5: 		<Platform Condition=" '$(Platform)' == '' ">AnyCPU</Platform>
6: 		<TargetFramework>net10.0</TargetFramework>
7: 		<Product>QuantConnect.Brokerages.Alpaca</Product>
8: 		<AssemblyName>QuantConnect.Brokerages.Alpaca</AssemblyName>
9: 		<RootNamespace>QuantConnect.Brokerages.Alpaca</RootNamespace>
```

[alpaca/QuantConnect.AlpacaBrokerage/QuantConnect.AlpacaBrokerage.csproj:28–43](https://github.com/QuantConnect/Lean.Brokerages.Alpaca/blob/f186471dc3a9b349e516a69fd75a603ffb5e1050/QuantConnect.AlpacaBrokerage/QuantConnect.AlpacaBrokerage.csproj#L28-L43)

```text
28: 	</ItemGroup>
29: 	<ItemGroup>
30: 		<PackageReference Include="Newtonsoft.Json" Version="13.0.2" />
31: 		<PackageReference Include="QuantConnect.Brokerages" Version="2.5.*" />
32: 		<PackageReference Include="QuantConnect.Lean.Engine" Version="2.5.*" />
33: 		<!--Dependencies of Alpaca.Markets.dll ref: https://github.com/QuantConnect/alpaca-trade-api-csharp/blob/master/Alpaca.Markets/Alpaca.Markets.csproj-->
34: 		<PackageReference Include="Polly" Version="8.6.3" />
35: 		<PackageReference Include="MessagePack" Version="3.1.7" />
36: 	</ItemGroup>
37: 
38: 	<ItemGroup>
39: 		<Reference Include="Alpaca.Markets">
40: 			<HintPath>Alpaca.Markets.dll</HintPath>
41: 		</Reference>
42: 		<None Update="Alpaca.Markets.dll" Pack="True">
43: 			<CopyToOutputDirectory>PreserveNewest</CopyToOutputDirectory>
```

[alpaca/QuantConnect.AlpacaBrokerage/AlpacaBrokerage.cs:1471–1492](https://github.com/QuantConnect/Lean.Brokerages.Alpaca/blob/f186471dc3a9b349e516a69fd75a603ffb5e1050/QuantConnect.AlpacaBrokerage/AlpacaBrokerage.cs#L1471-L1492)

```text
1471:         private static void ValidateSubscription()
1472:         {
1473:             try
1474:             {
1475:                 var productId = 347;
1476:                 var userId = Globals.UserId;
1477:                 var token = Globals.UserToken;
1478:                 var organizationId = Globals.OrganizationID;
1479:                 // Verify we can authenticate with this user and token
1480:                 var api = new ApiConnection(userId, token);
1481:                 if (!api.Connected)
1482:                 {
1483:                     throw new ArgumentException("Invalid api user id or token, cannot authenticate subscription.");
1484:                 }
1485:                 // Compile the information we want to send when validating
1486:                 var information = new Dictionary<string, object>()
1487:                 {
1488:                     {"productId", productId},
1489:                     {"machineName", Environment.MachineName},
1490:                     {"userName", Environment.UserName},
1491:                     {"domainName", Environment.UserDomainName},
1492:                     {"os", Environment.OSVersion}
```

[alpaca/QuantConnect.AlpacaBrokerage/AlpacaBrokerage.cs:1528–1537](https://github.com/QuantConnect/Lean.Brokerages.Alpaca/blob/f186471dc3a9b349e516a69fd75a603ffb5e1050/QuantConnect.AlpacaBrokerage/AlpacaBrokerage.cs#L1528-L1537)

```text
1528:                 // Create HTTP request
1529:                 using var request = ApiUtils.CreateJsonPostRequest("modules/license/read", information);
1530:                 api.TryRequest(request, out ModulesReadLicenseRead result);
1531:                 if (!result.Success)
1532:                 {
1533:                     throw new InvalidOperationException($"Request for subscriptions from web failed, Response Errors : {string.Join(',', result.Errors)}");
1534:                 }
1535: 
1536:                 var encryptedData = result.License;
1537:                 // Decrypt the data we received
```

[alpaca/QuantConnect.AlpacaBrokerage/AlpacaBrokerage.cs:1568–1596](https://github.com/QuantConnect/Lean.Brokerages.Alpaca/blob/f186471dc3a9b349e516a69fd75a603ffb5e1050/QuantConnect.AlpacaBrokerage/AlpacaBrokerage.cs#L1568-L1596)

```text
1568:                     }
1569:                 }
1570:                 // Validate our conditions
1571:                 if (!expirationDate.HasValue || !isValid.HasValue || !stamp.HasValue)
1572:                 {
1573:                     throw new InvalidOperationException("Failed to validate subscription.");
1574:                 }
1575: 
1576:                 var nowUtc = DateTime.UtcNow;
1577:                 var timeSpan = nowUtc - Time.UnixTimeStampToDateTime(stamp.Value);
1578:                 if (timeSpan > TimeSpan.FromHours(12))
1579:                 {
1580:                     throw new InvalidOperationException("Invalid API response.");
1581:                 }
1582:                 if (!isValid.Value)
1583:                 {
1584:                     throw new ArgumentException($"Your subscription is not valid, please check your product subscriptions on our website.");
1585:                 }
1586:                 if (expirationDate < nowUtc)
1587:                 {
1588:                     throw new ArgumentException($"Your subscription expired {expirationDate}, please renew in order to use this product.");
1589:                 }
1590:             }
1591:             catch (Exception e)
1592:             {
1593:                 Log.Error($"ValidateSubscription(): Failed during validation, shutting down. Error : {e.Message}");
1594:                 Environment.Exit(1);
1595:             }
1596:         }
```

## S18 — Official broker docs and publicly visible pricing

[qc-ib](https://www.quantconnect.com/docs/v2/lean-cli/live-trading/brokerages/interactive-brokers) (raw HTML SHA-256 `8573b328a9dc2c83b7e736bc3882a331b89c84cf37bcd16bf3937f6aea11e8ac`):

> To view the implementation of the IB brokerage integration, see the Lean.Brokerages.InteractiveBrokers repository . To use the CLI, you must be a member in an organization on a paid tier.

[qc-alpaca](https://www.quantconnect.com/docs/v2/lean-cli/live-trading/brokerages/alpaca) (raw HTML SHA-256 `4f1eb75536b9f1dd4c82e9ee3fba10026512b9ab1a49da0e3e2b8cc892ef70d6`):

> brokerage integration, see the Lean.Brokerages.Alpaca repository . To use the CLI, you must be a member in an organization on a paid tier.

[Pricing](https://www.quantconnect.com/pricing): inline JSON `packs`/`seats` gives Researcher Seat $10 monthly/$96 yearly and Pack $84 monthly/$888 yearly. The captured `moduleProducts` array lacks product 181 and 347. See `public_pricing_extract.json`; this absence cannot establish free entitlement.

IBKR docs additionally describe TWS/IB Gateway, account login/2FA, reconnect limits and an unsupported ARM Gateway path. Broker/data/API license and account terms are separate; no official license-service request or broker call was made.

## S19 — Nautilus only as the explicit challenger

[nautilus/README.md:24–31](https://github.com/nautechsystems/nautilus_trader/blob/c6e8f73f89dfdd49a5c6a2578173ff3e2057dfb1/README.md#L24-L31)

```text
24: - **Docs**: <https://nautilustrader.io/docs/>
25: - **Website**: <https://nautilustrader.io>
26: - **Support**: [support@nautilustrader.io](mailto:support@nautilustrader.io)
27: 
28: ## Introduction
29: 
30: NautilusTrader is an open-source, production-grade, Rust-native engine for multi-asset,
31: multi-venue trading systems.
```

[nautilus/README.md:113–126](https://github.com/nautechsystems/nautilus_trader/blob/c6e8f73f89dfdd49a5c6a2578173ff3e2057dfb1/README.md#L113-L126)

```text
113: | [Bybit](https://www.bybit.com)                             | `BYBIT`               | Crypto Exchange (CEX)   | ![status](https://img.shields.io/badge/stable-green)    | [Guide](docs/integrations/bybit.md)               |
114: | [CoinAPI](https://www.coinapi.io/?ref=nautilus)            | `COINAPI`             | Data Provider           | ![status](https://img.shields.io/badge/beta-yellow)     | [Guide](docs/integrations/coinapi.md)             |
115: | [Coinbase](https://coinbase.com)                           | `COINBASE`            | Crypto Exchange (CEX)   | ![status](https://img.shields.io/badge/stable-green)    | [Guide](docs/integrations/coinbase.md)            |
116: | [Databento](https://databento.com)                         | `DATABENTO`           | Data Provider           | ![status](https://img.shields.io/badge/stable-green)    | [Guide](docs/integrations/databento.md)           |
117: | [Deribit](https://www.deribit.com)                         | `DERIBIT`             | Crypto Exchange (CEX)   | ![status](https://img.shields.io/badge/stable-green)    | [Guide](docs/integrations/deribit.md)             |
118: | [Derive](https://www.derive.xyz)                           | `DERIVE`              | Crypto Exchange (DEX)   | ![status](https://img.shields.io/badge/stable-green)    | [Guide](docs/integrations/derive.md)              |
119: | [dYdX](https://dydx.trade)                                 | `DYDX`                | Crypto Exchange (DEX)   | ![status](https://img.shields.io/badge/stable-green)    | [Guide](docs/integrations/dydx.md)                |
120: | [FinFeed](https://www.finfeedapi.com/?ref=nautilus)        | `FINFEED`             | Data Provider           | ![status](https://img.shields.io/badge/building-orange) | -                                                 |
121: | [Hyperliquid](https://hyperliquid.xyz)                     | `HYPERLIQUID`         | Crypto Exchange (DEX)   | ![status](https://img.shields.io/badge/stable-green)    | [Guide](docs/integrations/hyperliquid.md)         |
122: | [Interactive Brokers](https://www.interactivebrokers.com)  | `INTERACTIVE_BROKERS` | Brokerage (multi-venue) | ![status](https://img.shields.io/badge/stable-green)    | [Guide](docs/integrations/interactive_brokers.md) |
123: | [Kalshi](https://kalshi.com)                               | `KALSHI`              | Prediction Market (CEX) | ![status](https://img.shields.io/badge/building-orange) | -                                                 |
124: | [Kraken](https://kraken.com)                               | `KRAKEN`              | Crypto Exchange (CEX)   | ![status](https://img.shields.io/badge/stable-green)    | [Guide](docs/integrations/kraken.md)              |
125: | [Lighter](https://lighter.xyz)                             | `LIGHTER`             | Crypto Exchange (DEX)   | ![status](https://img.shields.io/badge/stable-green)    | [Guide](docs/integrations/lighter.md)             |
126: | [Lighter on Robinhood](https://robinhoodchain.lighter.xyz) | `LIGHTER_ROBINHOOD`   | Crypto Exchange (DEX)   | ![status](https://img.shields.io/badge/stable-green)    | [Guide](docs/integrations/lighter.md)             |
```

[nautilus/README.md:302–308](https://github.com/nautechsystems/nautilus_trader/blob/c6e8f73f89dfdd49a5c6a2578173ff3e2057dfb1/README.md#L302-L308)

```text
302: 
303: #### Stable wheels
304: 
305: Stable wheels correspond to official releases of `nautilus_trader` on PyPI, and use standard
306: versioning. As on PyPI, the latest stable release is still on the 1.x line, whose Python API differs
307: from these v2 docs. This index also hosts development wheels, so `--pre` allows those versions too.
308: To install a specific 2.x release candidate, pin its version (`nautilus_trader==2.0.0rcN`).
```

[nautilus/python/pyproject.toml:18–25](https://github.com/nautechsystems/nautilus_trader/blob/c6e8f73f89dfdd49a5c6a2578173ff3e2057dfb1/python/pyproject.toml#L18-L25)

```text
18:   "Intended Audience :: Financial and Insurance Industry",
19:   "Intended Audience :: Science/Research",
20: ]
21: license = "LGPL-3.0-only"
22: license-files = ["LICENSE"]
23: readme = "../README.md"
24: requires-python = ">=3.13,<3.15"
25: dependencies = []
```

[nautilus/crates/model/src/instruments/equity.rs:40–95](https://github.com/nautechsystems/nautilus_trader/blob/c6e8f73f89dfdd49a5c6a2578173ff3e2057dfb1/crates/model/src/instruments/equity.rs#L40-L95)

```text
40: #[derive(Clone, Debug, Serialize, Deserialize)]
41: #[cfg_attr(
42:     feature = "python",
43:     pyo3::pyclass(module = "nautilus_trader.model", from_py_object)
44: )]
45: #[cfg_attr(
46:     feature = "python",
47:     pyo3_stub_gen::derive::gen_stub_pyclass(module = "nautilus_trader.model")
48: )]
49: pub struct Equity {
50:     /// The instrument ID.
51:     pub id: InstrumentId,
52:     /// The raw/local/native symbol for the instrument, assigned by the venue.
53:     pub raw_symbol: Symbol,
54:     /// The instruments International Securities Identification Number (ISIN).
55:     pub isin: Option<Ustr>,
56:     /// The futures contract currency.
57:     pub currency: Currency,
58:     /// The price decimal precision.
59:     pub price_precision: u8,
60:     /// The minimum price increment (tick size).
61:     pub price_increment: Price,
62:     /// The initial (order) margin requirement in percentage of order value.
63:     pub margin_init: Decimal,
64:     /// The maintenance (position) margin in percentage of position value.
65:     pub margin_maint: Decimal,
66:     /// The rounded lot unit size (standard/board).
67:     pub lot_size: Option<Quantity>,
68:     /// The maximum allowable order quantity.
69:     pub max_quantity: Option<Quantity>,
70:     /// The minimum allowable order quantity.
71:     pub min_quantity: Option<Quantity>,
72:     /// The maximum allowable quoted price.
73:     pub max_price: Option<Price>,
74:     /// The minimum allowable quoted price.
75:     pub min_price: Option<Price>,
76:     /// The registered variable tick scheme name.
77:     pub tick_scheme: Option<Ustr>,
78:     /// Additional instrument metadata as a JSON-serializable dictionary.
79:     pub info: Option<Params>,
80:     /// UNIX timestamp (nanoseconds) when the data event occurred.
81:     pub ts_event: UnixNanos,
82:     /// UNIX timestamp (nanoseconds) when the data object was initialized.
83:     pub ts_init: UnixNanos,
84: }
85: 
86: #[bon::bon]
87: impl Equity {
88:     #[expect(clippy::too_many_arguments)]
89:     fn new_checked(
90:         instrument_id: InstrumentId,
91:         raw_symbol: Symbol,
92:         isin: Option<Ustr>,
93:         currency: Currency,
94:         price_precision: u8,
95:         price_increment: Price,
```

## Source limits

Alpaca has no root `LICENSE` at the inspected path (request failed); source headers and README explicitly carry Apache-2.0. No claim is made about every bundled binary/dependency license. Current plugin prices and all-in broker entitlement cannot be inferred from engine/source licensing or public seat/pack prices. No runtime/binary, market-data or account validation was performed.
