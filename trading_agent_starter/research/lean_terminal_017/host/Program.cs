using System.Globalization;
using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using System.Security.Cryptography;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using QuantConnect;
using QuantConnect.Algorithm;
using QuantConnect.Algorithm.Framework.Portfolio;
using QuantConnect.Brokerages;
using QuantConnect.Brokerages.Backtesting;
using QuantConnect.Configuration;
using QuantConnect.Data;
using QuantConnect.Data.Market;
using QuantConnect.Data.UniverseSelection;
using QuantConnect.Interfaces;
using QuantConnect.Lean.Engine;
using QuantConnect.Lean.Engine.DataFeeds;
using QuantConnect.Lean.Engine.RealTime;
using QuantConnect.Lean.Engine.Results;
using QuantConnect.Lean.Engine.Server;
using QuantConnect.Lean.Engine.Setup;
using QuantConnect.Lean.Engine.TransactionHandlers;
using QuantConnect.Orders;
using QuantConnect.Packets;
using QuantConnect.Securities;
using QuantConnect.Util;

// Terminal-only fixture host. No private access, reflection, core modification or broker plugin.
// Native result sampling/publication is deliberately disabled: no performance/alpha metrics.
public static class Program
{
    public const string LeanPin = "d4cac37514427c84d40064cecbf3f0e6be4b0137";
    public static string Decimal(decimal value) => value.ToString("G29", CultureInfo.InvariantCulture);
    public static string Hash(byte[] bytes) => Convert.ToHexStringLower(SHA256.HashData(bytes));
    public static int Main(string[] args)
    {
        var output = new JObject { ["source_pin"] = LeanPin };
        try
        {
            if(args.Length != 3) throw new ArgumentException("fixture directory, case ID, output path required");
            var fixtureRoot=args[0];
            var manifest=JObject.Parse(File.ReadAllText(Path.Combine(fixtureRoot,"manifest.json")));
            foreach(var item in (JObject)manifest["sha256"]!)
                if(Hash(File.ReadAllBytes(Path.Combine(fixtureRoot,item.Key))) != (string)item.Value!)
                    throw new InvalidOperationException("Frozen fixture hash mismatch: "+item.Key);
            var inputBytes=File.ReadAllBytes(Path.Combine(fixtureRoot,"input.json"));
            var input=JObject.Parse(System.Text.Encoding.UTF8.GetString(inputBytes));
            var test=(JObject)((JArray)input["cases"]!).Single(x => (string)x["case_id"]! == args[1]);
            output["case_id"]=args[1]; output["input_sha256"]=Hash(inputBytes);
            output["fixture_manifest_sha256"]=Hash(File.ReadAllBytes(Path.Combine(fixtureRoot,"manifest.json")));
            var interfaces=NetworkInterface.GetAllNetworkInterfaces();
            if(interfaces.Any(x=>x.NetworkInterfaceType!=NetworkInterfaceType.Loopback))
                throw new InvalidOperationException("Runtime network is not loopback-only");
            string socketResult;
            using(var socket=new Socket(AddressFamily.InterNetwork,SocketType.Stream,ProtocolType.Tcp))
            {
                try { socket.Connect(new IPEndPoint(IPAddress.Parse("203.0.113.1"),9)); throw new InvalidOperationException("Network sentinel unexpectedly connected"); }
                catch(SocketException e) when(e.SocketErrorCode==SocketError.NetworkUnreachable || e.SocketErrorCode==SocketError.AccessDenied) { socketResult=e.SocketErrorCode.ToString(); }
            }
            output["network_denied"]=new JObject{["non_loopback_interfaces"]=0,["testnet_socket_result"]=socketResult};
            Config.Set("data-folder","/work/source/Data"); Config.Set("live-mode","false");
            Config.Set("results-destination-folder","/tmp/lean-results");
            Config.Set("log-handler","QuantConnect.Logging.ConsoleLogHandler");
            Config.Set("composer-dll-directory","/work/host/bin/Release/net10.0");
            var algorithm=new TerminalAlgorithm((JObject)input["shared"]!,test);
            var hours=MarketHoursDatabase.FromDataFolder();
            var permissions=new DataPermissionManager();
            var service=new SecurityService(algorithm.Portfolio.CashBook,hours,SymbolPropertiesDatabase.FromDataFolder(),algorithm,
                RegisteredSecurityDataTypesProvider.Null,new SecurityCacheProvider(algorithm.Portfolio),algorithm:algorithm);
            algorithm.Securities.SetSecurityService(service);
            var universeSelection=new UniverseSelection(algorithm,service,permissions,new DefaultDataProvider());
            var feed=new FixtureFeed(algorithm);
            var dataManager=new DataManager(feed,universeSelection,algorithm,algorithm.TimeKeeper,hours,false,RegisteredSecurityDataTypesProvider.Null,permissions);
            algorithm.SubscriptionManager.SetDataManager(dataManager);
            algorithm.Initialize(); algorithm.OnEndOfTimeStep(); algorithm.SetFinishedWarmingUp();
            var results=new LocalResults();
            var job=new BacktestNodePacket{BacktestId="terminal-fixture",Language=Language.CSharp,PeriodStart=algorithm.StartDate,PeriodFinish=algorithm.EndDate};
            using var brokerage=(TerminalBrokerage)new TerminalSetup(algorithm).CreateBrokerage(job,algorithm,out var factory);
            var transaction=new BacktestingTransactionHandler();
            algorithm.Transactions.SetOrderProcessor(transaction);
            transaction.Initialize(algorithm,brokerage,results);
            var realtime=new BacktestingRealTimeHandler();
            realtime.Setup(algorithm,job,results,null,null);
            algorithm.Schedule.SetEventSchedule(realtime);
            algorithm.SetStatus(AlgorithmStatus.Running); algorithm.SetLocked();
            var stream=new FixtureStream(algorithm,dataManager,universeSelection);
            var manager=new AlgorithmManager(false,job);
            try
            {
                manager.Run(job,algorithm,stream,transaction,results,realtime,new LocalLeanManager(),new CancellationTokenSource(),new PerformanceTrackingTool());
                if(algorithm.RunTimeError!=null) throw new InvalidOperationException("LEAN algorithm runtime error",algorithm.RunTimeError);
                if(!algorithm.EndObserved) throw new InvalidOperationException("Native AlgorithmManager end callback not reached");
                output["engine_status"]=algorithm.Status.ToString();
                output["events"]=algorithm.Events; output["snapshots"]=algorithm.Snapshots;
                output["native_order_events"]=JArray.FromObject(transaction.OrderEvents.Select(x=>new{order_id=x.OrderId,status=x.Status.ToString(),fill_quantity=Decimal(x.FillQuantity),fill_price=Decimal(x.FillPrice),fee=Decimal(x.OrderFee.Value.Amount),message=x.Message}));
                output["universe_branch"]=algorithm.UniverseBranch;
                output["conflict_blocked"]=algorithm.ConflictBlocked;
                output["execution_complete"]=true;
            }
            finally { transaction.Exit(); realtime.Exit(); dataManager.RemoveAllSubscriptions(); }
        }
        catch(Exception e)
        { output["execution_complete"]=false; output["technical_error"]=e.ToString(); }
        if(args.Length==3) File.WriteAllText(args[2],output.ToString(Formatting.None)+"\n");
        return (bool?)output["execution_complete"]==true ? 0 : 3;
    }
}

public sealed class TerminalSetup : BacktestingSetupHandler
{
    readonly TerminalAlgorithm fixture;
    public TerminalSetup(TerminalAlgorithm fixture) { this.fixture=fixture; }
    public override IBrokerage CreateBrokerage(AlgorithmNodePacket job,IAlgorithm algorithm,out IBrokerageFactory factory)
    { factory=new BacktestingBrokerageFactory(); return new TerminalBrokerage(fixture); }
}
public sealed class TerminalBrokerage : BacktestingBrokerage
{
    readonly TerminalAlgorithm fixture;
    public TerminalBrokerage(TerminalAlgorithm algorithm):base(algorithm) { fixture=algorithm; }
    protected override void OnDelistingNotification(DelistingNotificationEventArgs args)
    {
        fixture.Record("Notification:"+(fixture.Forward ? "Forwarded":"Intercepted"));
        if(fixture.Forward) base.OnDelistingNotification(args);
    }
}
// Only observer/output methods are suppressed; transaction/accounting/removal code is unchanged.
public sealed class LocalResults : BacktestingResultHandler
{
    public override void Sample(DateTime time) { }
    public override void ProcessSynchronousEvents(bool forceProcess=false) { }
    public override void SendStatusUpdate(AlgorithmStatus status,string message="") { }
    public override void OnSecuritiesChanged(SecurityChanges changes) { }
    public override void OnWarmupFinished() { }
}
public sealed class FrozenClock : ITimeProvider
{ public DateTime Time; public DateTime GetUtcNow()=>Time; }

public sealed class TerminalAlgorithm : QCAlgorithm
{
    public readonly JObject Shared,Case;
    public readonly JArray Events=new(),Snapshots=new();
    public DateTime Decision { get; }
    public readonly Symbol Instrument;
    public bool Forward => (bool)Case["forward_delisting_notification"]!;
    public bool Seeded,Terminal,Resolved,EndObserved,ConflictBlocked;
    public string UniverseBranch="";
    public Security Holding;
    public int Settlements;
    readonly Dictionary<string,string> admitted=new(StringComparer.Ordinal);
    readonly HashSet<int> delivered=new();
    public TerminalAlgorithm(JObject shared,JObject test)
    {
        Shared=shared;Case=test;
        Decision=DateTime.Parse((string)shared["decision_utc"]!,CultureInfo.InvariantCulture,DateTimeStyles.AdjustToUniversal|DateTimeStyles.AssumeUniversal);
        Instrument=new Symbol(SecurityIdentifier.GenerateEquity(new DateTime(2025,1,1),"AAA",Market.USA),"AAA");
    }
    public override void Initialize()
    {
        SetStartDate(2025,1,6);SetEndDate(2025,1,6);SetTimeZone(TimeZones.NewYork);SetCash(9000);
        SetBenchmark(time=>0m);SetDateTime(Decision.AddSeconds(-1));
        UniverseSettings.Resolution=Resolution.Minute;UniverseSettings.FillForward=false;
        UniverseSettings.DataNormalizationMode=DataNormalizationMode.Raw;UniverseSettings.MinimumTimeInUniverse=TimeSpan.Zero;
        if((string)Case["universe"]! == "user_defined")
            AddSecurity(Instrument,Resolution.Minute,fillForward:false,dataNormalizationMode:DataNormalizationMode.Raw);
        else
        {
            var u=QuantConnect.Symbol.Create("terminal-fixture-universe",SecurityType.Base,Market.USA);
            var config=new SubscriptionDataConfig(typeof(BaseDataCollection),u,Resolution.Minute,TimeZones.NewYork,TimeZones.NewYork,false,false,false);
            AddUniverse(new FuncUniverse(config,UniverseSettings,_=>new[]{Instrument}));
        }
        if((string)Case["fixture"]! == "Q02")
            Schedule.On(DateRules.On(2025,1,6),TimeRules.At(17,0,TimeZones.Utc),()=>DeliverRecords(7200));
    }
    public void Record(string kind,JObject payload=null)
    {
        Events.Add(new JObject{["kind"]=kind,["utc"]=UtcTime.ToString("yyyy-MM-ddTHH:mm:ss.fffffffZ",CultureInfo.InvariantCulture),["payload"]=payload});
    }
    public override void OnData(Slice slice)
    {
        if(Seeded || !Securities.ContainsKey(Instrument)) return;
        Holding=Securities[Instrument];
        Holding.Holdings.SetHoldings(100m,10m);
        Holding.Holdings.Target=new PortfolioTarget(Instrument,10m);
        Holding.SetMarketPrice(new Tick(Decision.AddSeconds(-1).ConvertFromUtc(TimeZones.NewYork),Instrument,100m,100m));
        Seeded=true;Record("Seed");
        UniverseBranch=string.Join(",",UniverseManager.Values.Where(u=>u.ContainsMember(Instrument)).Select(u=>u.GetType().Name).OrderBy(x=>x,StringComparer.Ordinal));
        LimitOrder(Instrument,2m,1m,tag:"buy2");LimitOrder(Instrument,-3m,1000m,tag:"sell3");
    }
    public override void OnDelistings(Delistings delistings)
    {
        foreach(var d in delistings.Values)
        {
            Record(d.Type.ToString());
            if(d.Type==DelistingType.Delisted){ Terminal=true;Record("UnresolvedTerminal"); }
        }
    }
    public override void OnOrderEvent(OrderEvent e)
    {
        var order=Transactions.GetOrderById(e.OrderId);
        if(e.Status==OrderStatus.Filled) Record("TradeFill:"+order.Tag,new JObject{["quantity"]=Program.Decimal(e.FillQuantity),["price"]=Program.Decimal(e.FillPrice),["fee"]=Program.Decimal(e.OrderFee.Value.Amount),["order_id"]=e.OrderId});
        else if(e.Status==OrderStatus.Submitted) Record("OrderSubmitted:"+order.Tag);
        else if(e.Status==OrderStatus.Canceled) Record("OrderCanceled:"+order.Tag);
        else if(e.Status==OrderStatus.Invalid) throw new InvalidOperationException("Fixture order invalid: "+e.Message);
    }
    void DeliverRecords(int offset)
    {
        var records=(JArray)Case["settlement_records"]!;
        for(var i=0;i<records.Count;i++)
            if((int)records[i]["delivery_offset_seconds"]! == offset && delivered.Add(i))
                AdmitSettlement((JObject)records[i]["payload"]!);
    }
    void AdmitSettlement(JObject evidence)
    {
        if(UtcTime<Decision.AddSeconds((int)evidence["available_offset_seconds"]!))
            throw new InvalidOperationException("Settlement before availability");
        var key=(string)evidence["event_id"]!+":"+(string)evidence["version"]!;
        var digest=Program.Hash(System.Text.Encoding.UTF8.GetBytes(evidence.ToString(Formatting.None)));
        if(admitted.TryGetValue(key,out var prior))
        {
            if(prior==digest) { Record("DuplicateIgnored"); return; }
            ConflictBlocked=true;Record("ConflictBlocked",new JObject{["reason"]="SAME_VERSION_CONFLICT",["evidence_sha256"]=digest});return;
        }
        if(!Terminal || Holding.Holdings.Quantity!=decimal.Parse((string)evidence["quantity"]!,CultureInfo.InvariantCulture))
            throw new InvalidOperationException("Settlement without retained terminal holding");
        var price=decimal.Parse((string)evidence["per_share"]!,CultureInfo.InvariantCulture);
        var cash=price*Holding.Holdings.Quantity;
        Portfolio.CashBook["USD"].AddAmount(cash);
        Holding.Holdings.AddNewProfit(cash-Holding.Holdings.AveragePrice*Holding.Holdings.Quantity);
        Holding.Holdings.SetHoldings(0m,0m);Holding.Holdings.Target=new PortfolioTarget(Instrument,0m);
        admitted.Add(key,digest);Resolved=true;Settlements++;
        Record("ActionSettlement",new JObject{["event_id"]=(string)evidence["event_id"]!,["evidence_sha256"]=digest,["amount"]=Program.Decimal(cash),["effective_utc"]=Decision.AddSeconds((int)evidence["effective_offset_seconds"]!).ToString("O"),["available_utc"]=Decision.AddSeconds((int)evidence["available_offset_seconds"]!).ToString("O")});
    }
    public void AfterFrame(DateTime frame)
    {
        if(frame==Decision.AddSeconds(7201)) DeliverRecords(7201);
        Snapshot(frame.ToString("yyyy-MM-ddTHH:mm:ss.fffffffZ",CultureInfo.InvariantCulture));
    }
    public void Snapshot(string phase)
    {
        var unknown=Terminal&&!Resolved;
        Snapshots.Add(new JObject{["phase"]=phase,["engine_quantity"]=Holding==null?null:Program.Decimal(Holding.Holdings.Quantity),["engine_security_present"]=Securities.ContainsKey(Instrument),["cash"]=Program.Decimal(Portfolio.CashBook["USD"].Amount),["realized_pnl"]=Resolved?Program.Decimal(Holding.Holdings.Profit):null,["realized_proceeds"]=Resolved?Program.Decimal(((string)Case["mode"]! =="zero" ?0m:375m)):null,["unresolved_claim"]=unknown?new JObject{["instrument_id"]="I1",["quantity"]="10",["status"]="UNKNOWN",["terminal_value"]=null}:null,["denominator"]=1,["failures"]=unknown?1:0,["scientific_nav"]=null,["nav_entry_blocked"]=unknown,["tradable"]=Holding?.IsTradable??false,["open_orders"]=Transactions.GetOpenOrders().Count(),["action_settlements"]=Settlements});
    }
    public override void OnEndOfAlgorithm(){EndObserved=true;Record("EndOfAlgorithm");Snapshot("end");}
}

// Frozen ingress only. Native DataManager, subscriptions, synchronization, removal and handler execute normally.
public sealed class FixtureFeed : IDataFeed
{
    readonly TerminalAlgorithm algorithm;
    public FixtureFeed(TerminalAlgorithm algorithm){this.algorithm=algorithm;}
    public bool IsActive=>true;
    public void Initialize(IAlgorithm a,AlgorithmNodePacket j,IResultHandler r,IMapFileProvider m,IFactorFileProvider f,IDataProvider p,IDataFeedSubscriptionManager s,IDataFeedTimeProvider t,IDataChannelProvider c) { }
    public Subscription CreateSubscription(SubscriptionRequest request)
    {
        var start=algorithm.UtcTime;
        var points=new List<SubscriptionData>();
        if(request.IsUniverseSubscription)
        {
            var data=new BaseDataCollection(start.ConvertFromUtc(TimeZones.NewYork),request.Configuration.Symbol,Array.Empty<BaseData>());
            points.Add(new SubscriptionData(data,start));
        }
        else if(request.Configuration.Symbol==algorithm.Instrument)
        {
            points.Add(new SubscriptionData(new Tick(algorithm.Decision.AddSeconds(-1).ConvertFromUtc(TimeZones.NewYork),algorithm.Instrument,100m,100m),algorithm.Decision.AddSeconds(-1)));
            points.Add(new SubscriptionData(new Delisting(algorithm.Instrument,algorithm.Decision.ConvertFromUtc(TimeZones.NewYork),100m,DelistingType.Warning),algorithm.Decision));
            points.Add(new SubscriptionData(new Delisting(algorithm.Instrument,algorithm.Decision.AddSeconds(60).ConvertFromUtc(TimeZones.NewYork),100m,DelistingType.Delisted),algorithm.Decision.AddSeconds(60)));
        }
        var offsets=new TimeZoneOffsetProvider(request.Configuration.ExchangeTimeZone,request.StartTimeUtc,request.EndTimeUtc);
        return new Subscription(request,points.GetEnumerator(),offsets);
    }
    public void RemoveSubscription(Subscription subscription) { }
    public void Exit() { }
}
public sealed class FixtureStream : ISynchronizer
{
    readonly TerminalAlgorithm algorithm;readonly DataManager manager;readonly UniverseSelection selection;
    public FixtureStream(TerminalAlgorithm a,DataManager m,UniverseSelection s){algorithm=a;manager=m;selection=s;}
    public IEnumerable<TimeSlice> StreamData(CancellationToken cancellationToken)
    {
        var clock=new FrozenClock{Time=algorithm.Decision.AddSeconds(-1)};
        var sync=new SubscriptionSynchronizer(selection,new PerformanceTrackingTool());
        sync.SetTimeProvider(clock);sync.SetTimeSliceFactory(new TimeSliceFactory(algorithm.TimeZone));
        sync.SubscriptionFinished+=(sender,subscription)=>manager.RemoveSubscription(subscription.Configuration);
        using var stream=sync.Sync(manager.DataFeedSubscriptions,cancellationToken).GetEnumerator();
        foreach(var offset in (JArray)algorithm.Shared["frame_offsets_seconds"]!)
        {
            clock.Time=algorithm.Decision.AddSeconds((int)offset);
            if(!stream.MoveNext())throw new InvalidOperationException("Native synchronizer ended early");
            yield return stream.Current;
            algorithm.AfterFrame(clock.Time);
            if(algorithm.ConflictBlocked)yield break;
        }
    }
}
