# Decisive official source excerpts

Captured 2026-10-17 UTC; static inspection only. Full-file hashes in execution_sources.json.

## lean/Engine/TransactionHandlers/BrokerageTransactionHandler.cs:1689

https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Engine/TransactionHandlers/BrokerageTransactionHandler.cs#L1689

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
```

## lean/Engine/Setup/BacktestingSetupHandler.cs:118

https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Engine/Setup/BacktestingSetupHandler.cs#L118

```text
118:         /// <summary>
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
130:
```

## lean/Brokerages/Brokerage.cs:311

https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Brokerages/Brokerage.cs#L311

```text
311:         }
312:
313:         /// <summary>
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
```

## lean/Engine/TransactionHandlers/BacktestingTransactionHandler.cs:43

https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Engine/TransactionHandlers/BacktestingTransactionHandler.cs#L43

```text
43:         /// Creates a new BacktestingTransactionHandler using the BacktestingBrokerage
44:         /// </summary>
45:         /// <param name="algorithm">The algorithm instance</param>
46:         /// <param name="brokerage">The BacktestingBrokerage</param>
47:         /// <param name="resultHandler"></param>
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
```

## lean/Brokerages/Backtesting/BacktestingBrokerage.cs:646

https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Brokerages/Backtesting/BacktestingBrokerage.cs#L646

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
671:
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
705:
706:         private void RemoveOrders(List<Order> orders, OrderStatus orderStatus, string message = "")
707:         {
708:             var orderEvents = new List<OrderEvent>(orders.Count);
709:             for (var i = 0; i < orders.Count; i++)
710:             {
```

## lean/Common/Orders/Fills/EquityFillModel.cs:124

https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/Orders/Fills/EquityFillModel.cs#L124

```text
124:         public override OrderEvent MarketFill(Security asset, MarketOrder order)
125:         {
126:             //Default order event to return.
127:             var utcTime = asset.LocalTime.ConvertToUtc(asset.Exchange.TimeZone);
128:             var fill = new OrderEvent(order, utcTime, OrderFee.Zero);
129:
130:             if (order.Status == OrderStatus.Canceled) return fill;
131:
132:             // Make sure the exchange is open/normal market hours before filling
133:             if (!IsExchangeOpen(asset, false)) return fill;
134:
135:             // Calculate the model slippage: e.g. 0.01c
136:             var slip = asset.SlippageModel.GetSlippageApproximation(asset, order);
137:
138:             // Fetch the subscription configs once and reuse them for both the best-effort price lookup and the
139:             // stale-data check below.
140:             var subscriptionConfigs = GetSubscriptionDataConfigs(asset);
141:
142:             // The best-effort price only considers the data types sent to the algorithm (non-internal subscriptions).
143:             var subscribedTypes = GetSubscribedTypes(asset, subscriptionConfigs);
144:
145:             var fillMessage = string.Empty;
146:             var stalePrice = false;
147:             var staleDataEndTimeUtc = default(DateTime);
148:             var fillPrice = 0m;
149:
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
176:             fill.Message = fillMessage;
```

## lean/Common/Orders/Fills/EquityFillModel.cs:780

https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/Orders/Fills/EquityFillModel.cs#L780

```text
780:             var bestEffortAskPrice = 0m;
781:
782:             // Define the cut off time to get the best effort bid or ask and whether the price is stale
783:             var localOrderTime = orderTime.ConvertFromUtc(asset.Exchange.TimeZone);
784:             var cutOffTime = localOrderTime.Add(-Parameters.StalePriceTimeSpan);
785:
786:             subscribedTypes ??= GetSubscribedTypes(asset);
787:
788:             List<Tick> ticks = null;
789:             var isTickSubscribed = subscribedTypes.Contains(typeof(Tick));
790:
791:             if (isTickSubscribed)
792:             {
793:                 ticks = asset.Cache.GetAll<Tick>().ToList();
794:
795:                 var quote = ticks.LastOrDefault(x => x.TickType == TickType.Quote && x.AskPrice > 0);
796:                 if (quote != null)
797:                 {
798:                     if (quote.EndTime >= cutOffTime)
799:                     {
800:                         return quote.AskPrice;
801:                     }
802:
803:                     baseData = quote;
804:                     bestEffortAskPrice = quote.AskPrice;
805:                     message = Messages.EquityFillModel.FilledWithQuoteTickData(asset, quote);
806:                 }
807:             }
808:
809:             if (subscribedTypes.Contains(typeof(QuoteBar)))
810:             {
811:                 var quoteBar = asset.Cache.GetData<QuoteBar>();
812:                 if (quoteBar != null && (baseData == null || quoteBar.EndTime > baseData.EndTime))
813:                 {
814:                     if (quoteBar.EndTime >= cutOffTime)
815:                     {
816:                         return quoteBar.Ask?.Close ?? quoteBar.Close;
817:                     }
818:
819:                     baseData = quoteBar;
820:                     bestEffortAskPrice = quoteBar.Ask?.Close ?? quoteBar.Close;
821:                     message = Messages.EquityFillModel.FilledWithQuoteBarData(asset, quoteBar);
822:                 }
823:             }
824:
825:             if (isTickSubscribed)
826:             {
827:                 var trade = ticks.LastOrDefault(x => x.TickType == TickType.Trade);
828:                 if (trade != null && (baseData == null || trade.EndTime > baseData.EndTime))
829:                 {
830:                     message = Messages.EquityFillModel.FilledWithTradeTickData(asset, trade);
831:
832:                     if (trade.EndTime >= cutOffTime)
833:                     {
834:                         return trade.Price;
835:                     }
836:
837:                     baseData = trade;
838:                     bestEffortAskPrice = trade.Price;
839:                 }
840:             }
841:
842:             if (subscribedTypes.Contains(typeof(TradeBar)))
843:             {
844:                 var tradeBar = asset.Cache.GetData<TradeBar>();
845:                 if (tradeBar != null && (baseData == null || tradeBar.EndTime > baseData.EndTime))
846:                 {
847:                     message = Messages.EquityFillModel.FilledWithTradeBarData(asset, tradeBar);
848:
849:                     if (tradeBar.EndTime >= cutOffTime)
850:                     {
851:                         return tradeBar.Close;
852:                     }
853:
854:                     baseData = tradeBar;
855:                     bestEffortAskPrice = tradeBar.Close;
```

## lean/Common/Brokerages/DefaultBrokerageModel.cs:252

https://github.com/QuantConnect/Lean/blob/d4cac37514427c84d40064cecbf3f0e6be4b0137/Common/Brokerages/DefaultBrokerageModel.cs#L252

```text
252:         public virtual IFeeModel GetFeeModel(Security security)
253:         {
254:             switch (security.Type)
255:             {
256:                 case SecurityType.Base:
257:                 case SecurityType.Forex:
258:                 case SecurityType.Cfd:
259:                 case SecurityType.Crypto:
260:                 case SecurityType.CryptoFuture:
261:                 case SecurityType.Index:
262:                     return new ConstantFeeModel(0m);
263:
264:                 case SecurityType.Equity:
265:                 case SecurityType.Option:
266:                 case SecurityType.Future:
267:                 case SecurityType.FutureOption:
268:                     return new InteractiveBrokersFeeModel();
269:
270:                 case SecurityType.Commodity:
271:                 default:
272:                     return new ConstantFeeModel(0m);
273:             }
274:         }
275:
276:         /// <summary>
277:         /// Gets a new slippage model that represents this brokerage's fill slippage behavior
278:         /// </summary>
279:         /// <param name="security">The security to get a slippage model for</param>
280:         /// <returns>The new slippage model for this brokerage</returns>
281:         public virtual ISlippageModel GetSlippageModel(Security security)
282:         {
283:             return NullSlippageModel.Instance;
284:         }
```

## lean-alpaca/QuantConnect.AlpacaBrokerage/AlpacaBrokerage.cs:172

https://github.com/QuantConnect/Lean.Brokerages.Alpaca/blob/f186471dc3a9b349e516a69fd75a603ffb5e1050/QuantConnect.AlpacaBrokerage/AlpacaBrokerage.cs#L172

```text
172:         private void Initialize(string apiKey, string apiKeySecret, string accessToken, bool isPaperTrading, IOrderProvider orderProvider, ISecurityProvider securityProvider)
173:         {
174:             if (_isInitialized)
175:             {
176:                 return;
177:             }
178:             _isInitialized = true;
179:             ValidateSubscription();
180:
181:             SecurityKey tradingSecretKey = null;
182:             if (!string.IsNullOrEmpty(accessToken))
```

## lean-alpaca/QuantConnect.AlpacaBrokerage/AlpacaBrokerage.cs:1471

https://github.com/QuantConnect/Lean.Brokerages.Alpaca/blob/f186471dc3a9b349e516a69fd75a603ffb5e1050/QuantConnect.AlpacaBrokerage/AlpacaBrokerage.cs#L1471

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
1493:                 };
1494:                 // IP and Mac Address Information
1495:                 try
1496:                 {
1497:                     var interfaceDictionary = new List<Dictionary<string, object>>();
1498:                     foreach (var nic in NetworkInterface.GetAllNetworkInterfaces().Where(nic => nic.OperationalStatus == OperationalStatus.Up))
1499:                     {
1500:                         var interfaceInformation = new Dictionary<string, object>();
```

## lean-alpaca/QuantConnect.AlpacaBrokerage/AlpacaBrokerage.cs:1525

https://github.com/QuantConnect/Lean.Brokerages.Alpaca/blob/f186471dc3a9b349e516a69fd75a603ffb5e1050/QuantConnect.AlpacaBrokerage/AlpacaBrokerage.cs#L1525

```text
1525:                 {
1526:                     information.Add("organizationId", organizationId);
1527:                 }
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
1538:                 DateTime? expirationDate = null;
```

## lean-alpaca/QuantConnect.AlpacaBrokerage/AlpacaBrokerage.cs:1570

https://github.com/QuantConnect/Lean.Brokerages.Alpaca/blob/f186471dc3a9b349e516a69fd75a603ffb5e1050/QuantConnect.AlpacaBrokerage/AlpacaBrokerage.cs#L1570

```text
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
1597:     }
```

## lean-ib/QuantConnect.InteractiveBrokersBrokerage/InteractiveBrokersBrokerage.cs:1463

https://github.com/QuantConnect/Lean.Brokerages.InteractiveBrokers/blob/fb86123c7ea07c3e9d02d56ed7476675e3e4578a/QuantConnect.InteractiveBrokersBrokerage/InteractiveBrokersBrokerage.cs#L1463

```text
1463:             string financialAdvisorsGroupFilter = default)
1464:         {
1465:             if (_isInitialized)
1466:             {
1467:                 return;
1468:             }
1469:
1470:             ValidateSubscription();
1471:
1472:             _isInitialized = true;
1473:             _loadExistingHoldings = loadExistingHoldings;
1474:             _algorithm = algorithm;
```

## lean-ib/QuantConnect.InteractiveBrokersBrokerage/InteractiveBrokersBrokerage.cs:6092

https://github.com/QuantConnect/Lean.Brokerages.InteractiveBrokers/blob/fb86123c7ea07c3e9d02d56ed7476675e3e4578a/QuantConnect.InteractiveBrokersBrokerage/InteractiveBrokersBrokerage.cs#L6092

```text
6092:
6093:         /// <summary>
6094:         /// Validate the user of this project has permission to be using it via our web API.
6095:         /// </summary>
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
6118:                 };
```

## lean-ib/QuantConnect.InteractiveBrokersBrokerage/InteractiveBrokersBrokerage.cs:6148

https://github.com/QuantConnect/Lean.Brokerages.InteractiveBrokers/blob/fb86123c7ea07c3e9d02d56ed7476675e3e4578a/QuantConnect.InteractiveBrokersBrokerage/InteractiveBrokersBrokerage.cs#L6148

```text
6148:                 // Include our OrganizationId is specified
6149:                 if (!string.IsNullOrEmpty(organizationId))
6150:                 {
6151:                     information.Add("organizationId", organizationId);
6152:                 }
6153:                 // Create HTTP request
6154:                 using var request = ApiUtils.CreateJsonPostRequest("modules/license/read", information);
6155:                 api.TryRequest(request, out ModulesReadLicenseRead result);
6156:                 if (!result.Success)
6157:                 {
6158:                     throw new InvalidOperationException($"Request for subscriptions from web failed, Response Errors : {string.Join(',', result.Errors)}");
6159:                 }
6160:
6161:                 var encryptedData = result.License;
6162:                 // Decrypt the data we received
```

## lean-ib/QuantConnect.InteractiveBrokersBrokerage/InteractiveBrokersBrokerage.cs:6192

https://github.com/QuantConnect/Lean.Brokerages.InteractiveBrokers/blob/fb86123c7ea07c3e9d02d56ed7476675e3e4578a/QuantConnect.InteractiveBrokersBrokerage/InteractiveBrokersBrokerage.cs#L6192

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
6222:
```

## nautilus-stable/RELEASES.md:1

https://github.com/nautechsystems/nautilus_trader/blob/27a8e54e7ac3c57d6cbf8891f0283dfbaee97317/RELEASES.md#L1

```text
1: # NautilusTrader 1.231.0 Beta
2:
3: Released on 2nd August 2026 (UTC).
4:
5: ### NautilusTrader v2 transition notice
6:
7: This release is intended to be the final NautilusTrader `1.x` release with support for the legacy
8: Cython v1 core. If final validation finds a serious blocker, maintainers may take another `1.x`
9: release rather than force the cutover.
10:
11: The v2 Rust + PyO3 runtime has reached the release-candidate stage for the supported
12: workflows: Python strategy authoring, backtesting, live operation, core risk and execution,
13: portfolio/accounting, data catalog usage, and the current adapter set. Some lower-use and newer
14: surfaces remain deferred, and those are tracked in the
15: [v2 roadmap](https://github.com/nautechsystems/nautilus_trader/issues/4042) rather than treated
16: as blockers for the cutover.
17:
18: After this release, `develop` will move to v2-only. The legacy v1 core will move to a
19: `develop_v1` branch, where maintainers will accept critical security backports for approximately
20: three months after the v2 cutover. New feature work will target v2.
21:
22: The paired `2.0.0rc2` wheels are being released alongside `1.231.0` for community testing with
23: normal `--pre` installation. Follow‑up `2.0.0rcN` wheels are likely to ship at a higher cadence
24: than normal releases as feedback arrives, before the final `2.0.0` release.
25:
26: #### Migration contracts
27:
28: The v2 cutover makes the Rust + PyO3 package the primary path for new installs and source builds.
29: In the current checkout it lives under `python/` and uses `python/.venv`; the root package and root
30: `.venv` still provide the legacy v1 Cython environment. Both packages import as
31: `nautilus_trader`, so test the migration in a separate virtual environment. See
32: [Migrate from v1 to v2](MIGRATION_V2.md) for the current imports and build commands.
33:
34: The accepted v2 contract differences are native `CustomData` without v1 wrapper semantics,
35: `OptionGreeks` cache writes, no Python `Bar.is_revision`, and a cross-zero `Position.apply` entry
36: price that resets to the flipping fill. V2 also prefers mark prices by default. Catalog order-event
37: data written before `activation_price` and `OrderFilled.info` were added is not readable with the new
38: schema and must be regenerated or migrated before an in-place upgrade. `OrderFillVoided` replay
39: requires the referenced fill locally before reopening and treats `VOIDED` as terminal. Regenerate
40: v2 order streams that contain a reopened correction before its referenced fill, or a cancel or
```

## nautilus/RELEASES.md:1

https://github.com/nautechsystems/nautilus_trader/blob/68bcfc778cf1635ee26e96225b2cb596b721c8cb/RELEASES.md#L1

```text
1: # NautilusTrader 2.0.0rc8
2:
3: Released on TBD (UTC).
4:
5: ### Enhancements
6:
7: ### Breaking Changes
8:
9: - Removed Polymarket `FeeRateResponse::to_rate` and Gamma `set_clob_client` and `clob_client` methods
10: - Changed emulated releases to undergo risk checks; use `REDUCING` for eligible exits, as `HALTED` denies stops
11: - Changed order-list validation to deny unsent siblings; retry with new IDs (#5336), thanks @imbolc
12: - Changed Hyperliquid `UpdateIsolatedMargin`: replace `delta` with `is_buy` and `ntli` (signed millionths)
13:
14: ### Security
15:
16: - Fixed HTTP `Referer` headers exposing URL paths and query parameters on cross-origin redirects
17: - Fixed Feather run recovery modifying files outside the catalog through path traversal or symlinks
18: - Fixed Hyperliquid private WebSocket parse errors exposing account data in logs
19:
20: ### Fixes
21:
22: - Fixed startup reconciliation leaving orders partially filled after venue quantity reductions
23: - Fixed risk denials for released orders and cleanup of their contingent orders
24: - Fixed Architect AX closed-order reports preceding their fills during reconciliation
25: - Fixed Binance Futures HTTP order reports using update time as acceptance time
26: - Fixed Binance spot SBE exponent overflow aborting user-data decode (#5320), thanks @zifulifufu
27: - Fixed Hyperliquid leverage and isolated-margin request serialization and signing
28: - Fixed Hyperliquid WebSocket readiness being published before handler initialization
29: - Fixed Interactive Brokers small-lot entry prices after commission rounding (#5327), thanks @bebop23
30: - Fixed Interactive Brokers futures expiry times blocking market data (#5318), thanks @chaneyka1
31: - Fixed Interactive Brokers quote sizes dropped by float rounding (#5318), thanks @chaneyka1
32: - Fixed Interactive Brokers stocks ignoring `symbol_to_mic_venue` (#5330), thanks @mmatvien
33: - Fixed Kraken Futures batch edits sending `orderId` instead of `order_id` (#5312), thanks @zhaow-de
34: - Fixed Kraken Futures client order IDs shortened to 18 characters (#5312), thanks @zhaow-de
35: - Fixed Lighter funding rates 100x too high and missing the live interval (#5338), thanks @dxwil
36: - Fixed Lighter order lookups using the wrong client order ID after a collision and restart
37: - Fixed empty and incomplete OKX historical bar responses (#5339), thanks for reporting @AlphaTraderK
38: - Fixed OKX USD-margined futures and swaps routed as spreads (#5337), thanks for reporting @michalismeng
39: - Fixed Polymarket cancels lost while submit responses register venue order IDs
40: - Fixed Polymarket `price_change` quotes carrying sizes from different price levels
41: - Fixed Polymarket stale book levels after resubscribing with effective deltas enabled
42: - Fixed Polymarket loading, request caching, and execution lookup cleanup for open markets past `endDate`
```

## nautilus-stable/pyproject.toml:1

https://github.com/nautechsystems/nautilus_trader/blob/27a8e54e7ac3c57d6cbf8891f0283dfbaee97317/pyproject.toml#L1

```text
1: [project]
2: name = "nautilus_trader"
3: version = "1.231.0"
4: description = "Production-grade Rust-native trading engine with deterministic event-driven architecture"
5: authors = [{ name = "Nautech Systems", email = "info@nautechsystems.io" }]
6: classifiers = [
7:   "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
8:   "Operating System :: OS Independent",
9:   "Development Status :: 4 - Beta",
10:   "Programming Language :: Python :: 3",
11:   "Programming Language :: Python :: 3.12",
12:   "Programming Language :: Python :: 3.13",
13:   "Programming Language :: Python :: 3.14",
14:   "Topic :: Software Development :: Libraries",
15:   "Topic :: Software Development :: Libraries :: Python Modules",
16:   "Topic :: Scientific/Engineering",
17:   "Topic :: Office/Business :: Financial",
18:   "Topic :: Office/Business :: Financial :: Investment",
19:   "Intended Audience :: Developers",
20:   "Intended Audience :: Financial and Insurance Industry",
21:   "Intended Audience :: Science/Research",
22: ]
23: license = { text = "LGPL-3.0-or-later" }
24: readme = "README.md"
25: requires-python = ">=3.12,<3.15"
26: dependencies = [
27:   "click>=8.4.1,<9.0.0",
28:   "fsspec>=2026.2.0,<=2026.2.0",
29:   "msgspec>=0.21.1,<1.0.0",
30:   "numpy>=1.26.4",
31:   "pandas>=2.3.3,<4.0.0",
32:   "portion>=2.6.1",
33:   "pyarrow>=25.0.0",
34:   "pytz>=2026.2",
35:   "tzdata>=2026.3",
36:   "tqdm>=4.68.4,<5.0.0",
37:   "uvloop==0.22.1,<1.0.0; sys_platform != \"win32\"", # Pinned to 0.22.1 for stability
38: ]
39:
40: [project.urls]
```

## nautilus-stable/pyproject.toml:90

https://github.com/nautechsystems/nautilus_trader/blob/27a8e54e7ac3c57d6cbf8891f0283dfbaee97317/pyproject.toml#L90

```text
90: ]
91:
92: [dependency-groups]
93: dev = [
94:   "cython==3.2.9", # Pinned to 3.2.9 for stability
95:   "jupytext>=1.19.3,<2.0.0",
96:   "setuptools>=83",
97:   "mypy==1.20.2,<2.0.0", # Pinned to 1.20.2 (keep in line with .pre-commit-config.yaml)
98:   "pandas-stubs>=2.3.3,<4.0.0",
99:   "ruff==0.16.0", # Pinned to 0.16.0 (keep in line with .pre-commit-config.yaml)
100:   "types-pytz>=2026.2,<2027.0",
101:   "types-toml>=0.10.8,<1.0.0",
102: ]
```

## nautilus/python/pyproject.toml:15

https://github.com/nautechsystems/nautilus_trader/blob/68bcfc778cf1635ee26e96225b2cb596b721c8cb/python/pyproject.toml#L15

```text
15:   "Topic :: Office/Business :: Financial",
16:   "Topic :: Office/Business :: Financial :: Investment",
17:   "Intended Audience :: Developers",
18:   "Intended Audience :: Financial and Insurance Industry",
19:   "Intended Audience :: Science/Research",
20: ]
21: license = "LGPL-3.0-only"
22: license-files = ["LICENSE"]
23: readme = "../README.md"
24: requires-python = ">=3.13,<3.15"
25: dependencies = []
26:
27: [project.optional-dependencies]
28: visualization = [
```

## nautilus-stable/nautilus_trader/backtest/config.py:457

https://github.com/nautechsystems/nautilus_trader/blob/27a8e54e7ac3c57d6cbf8891f0283dfbaee97317/nautilus_trader/backtest/config.py#L457

```text
457: class FillModelConfig(NautilusConfig, frozen=True):
458:     """
459:     Configuration for ``FillModel`` instances.
460:
461:     Parameters
462:     ----------
463:     prob_fill_on_limit : float, default 1.0
464:         The probability of limit order filling if the market rests on its price.
465:     prob_slippage : float, default 0.0
466:         The probability of order fill prices slipping by one tick.
467:     random_seed : int, optional
468:         The random seed (if None then no random seed).
469:
470:     """
471:
472:     prob_fill_on_limit: float = 1.0
473:     prob_slippage: float = 0.0
474:     random_seed: int | None = None
475:
```

## nautilus-stable/nautilus_trader/backtest/engine.pyx:635

https://github.com/nautechsystems/nautilus_trader/blob/27a8e54e7ac3c57d6cbf8891f0283dfbaee97317/nautilus_trader/backtest/engine.pyx#L635

```text
635:             modules = []
636:
637:         if margin_model is None:
638:             margin_model = LeveragedMarginModel()
639:
640:         if fill_model is None:
641:             fill_model = FillModel()
642:
643:         if fee_model is None:
644:             fee_model = MakerTakerFeeModel()
645:
646:         Condition.not_none(venue, "venue")
647:         Condition.not_in(venue, self._venues, "venue", "_venues")
648:         Condition.not_empty(starting_balances, "starting_balances")
649:         Condition.list_type(modules, SimulationModule, "modules")
650:         Condition.type(fill_model, FillModel, "fill_model")
651:         Condition.type(fee_model, FeeModel, "fee_model")
652:
```

## nautilus-stable/nautilus_trader/risk/engine.pyx:76

https://github.com/nautechsystems/nautilus_trader/blob/27a8e54e7ac3c57d6cbf8891f0283dfbaee97317/nautilus_trader/risk/engine.pyx#L76

```text
76: cdef class RiskEngine(Component):
77:     """
78:     Provides a high-performance risk engine.
79:
80:     The `RiskEngine` is responsible for global strategy and portfolio risk
81:     within the platform. This includes both pre-trade risk checks and post-trade
82:     risk monitoring.
83:
84:     Possible trading states:
85:      - ``ACTIVE`` (trading is enabled).
86:      - ``REDUCING`` (only new orders or updates which reduce an open position are allowed).
87:      - ``HALTED`` (all trading commands except cancels are denied).
88:
89:     Parameters
90:     ----------
```

## nautilus-stable/nautilus_trader/trading/trader.py:817

https://github.com/nautechsystems/nautilus_trader/blob/27a8e54e7ac3c57d6cbf8891f0283dfbaee97317/nautilus_trader/trading/trader.py#L817

```text
817:     def save(self) -> None:
818:         """
819:         Save all actor and strategy states to the cache.
820:         """
821:         for actor in self._actors.values():
822:             self._cache.update_actor(actor)
823:
824:         for strategy in self._strategies.values():
825:             self._cache.update_strategy(strategy)
826:
827:     def load(self) -> None:
828:         """
829:         Load all actor and strategy states from the cache.
830:         """
831:         for actor in self._actors.values():
832:             self._cache.load_actor(actor)
833:
834:         for strategy in self._strategies.values():
835:             self._cache.load_strategy(strategy)
836:
837:     def check_residuals(self) -> None:
```

## nautilus-stable/nautilus_trader/model/instruments/equity.pyx:92

https://github.com/nautechsystems/nautilus_trader/blob/27a8e54e7ac3c57d6cbf8891f0283dfbaee97317/nautilus_trader/model/instruments/equity.pyx#L92

```text
92:         Quantity lot_size not None,
93:         uint64_t ts_event,
94:         uint64_t ts_init,
95:         max_quantity: Quantity | None = None,
96:         min_quantity: Quantity | None = None,
97:         margin_init: Decimal | None = None,
98:         margin_maint: Decimal | None = None,
99:         maker_fee: Decimal | None = None,
100:         taker_fee: Decimal | None = None,
101:         str isin: str | None = None,
102:         str tick_scheme_name = None,
103:         dict info = None,
104:     ) -> None:
105:         if isin is not None:
106:             Condition.valid_string(isin, "isin")
107:         super().__init__(
108:             instrument_id=instrument_id,
109:             raw_symbol=raw_symbol,
110:             asset_class=AssetClass.EQUITY,
111:             instrument_class=InstrumentClass.SPOT,
112:             quote_currency=currency,
113:             is_inverse=False,
114:             price_precision=price_precision,
115:             size_precision=0,  # No fractional units
116:             price_increment=price_increment,
117:             size_increment=Quantity.from_int_c(1),
118:             multiplier=Quantity.from_int_c(1),
119:             lot_size=lot_size,
120:             max_quantity=max_quantity,
121:             min_quantity=min_quantity,
122:             max_notional=None,
123:             min_notional=None,
124:             max_price=None,
125:             min_price=None,
126:             margin_init=margin_init or Decimal(0),
127:             margin_maint=margin_maint or Decimal(0),
128:             maker_fee=maker_fee or Decimal(0),
129:             taker_fee=taker_fee or Decimal(0),
130:             ts_event=ts_event,
131:             ts_init=ts_init,
132:             tick_scheme_name=tick_scheme_name,
133:             info=info,
134:         )
135:
136:         self.isin = isin
137:
138:     @staticmethod
139:     cdef Equity from_dict_c(dict values):
140:         Condition.not_none(values, "values")
```

## nautilus-stable/nautilus_trader/adapters/interactive_brokers/client/client.py:25

https://github.com/nautechsystems/nautilus_trader/blob/27a8e54e7ac3c57d6cbf8891f0283dfbaee97317/nautilus_trader/adapters/interactive_brokers/client/client.py#L25

```text
25:
26: from ibapi import comm
27: from ibapi.client import EClient
28: from ibapi.commission_and_fees_report import CommissionAndFeesReport
29: from ibapi.common import PROTOBUF_MSG_ID
30: from ibapi.common import BarData
31: from ibapi.const import MAX_MSG_LEN
32: from ibapi.const import NO_VALID_ID
33: from ibapi.errors import BAD_LENGTH
34: from ibapi.execution import Execution
35: from ibapi.server_versions import MIN_SERVER_VER_PROTOBUF
36: from ibapi.utils import current_fn_name
```
