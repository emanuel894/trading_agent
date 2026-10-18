using System.Globalization;
using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using System.Security.Cryptography;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using QuantConnect;
using QuantConnect.Algorithm;
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
using QuantConnect.Orders.Fees;
using QuantConnect.Orders.Fills;
using QuantConnect.Packets;
using QuantConnect.Securities;
using QuantConnect.Util;

// Synthetic qualification only. Native engine/order/portfolio code remains unchanged.
// .NET clocks pace envelopes; int64 source clocks govern causality and validity.
public static class Program
{
    public const string Pin="d4cac37514427c84d40064cecbf3f0e6be4b0137";
    public static string Num(decimal x)=>x.ToString("G29",CultureInfo.InvariantCulture);
    public static string Hash(byte[] x)=>Convert.ToHexStringLower(SHA256.HashData(x));
    public static long Ns(JToken x)=>(long)x;
    public static long Ceiling(long ns)=>checked(((ns+99)/100)*100);
    public static DateTime Time(long ns)=>DateTime.UnixEpoch.AddTicks(Ceiling(ns)/100);
    public static int Main(string[] args)
    {
        var output=new JObject{["source_pin"]=Pin};
        try
        {
            if(args.Length!=3)throw new ArgumentException("fixture directory, case ID, output file required");
            var root=args[0];var bytes=File.ReadAllBytes(Path.Combine(root,"input.json"));
            var manifestBytes=File.ReadAllBytes(Path.Combine(root,"manifest.json"));
            var manifest=JObject.Parse(System.Text.Encoding.UTF8.GetString(manifestBytes));
            foreach(var pair in (JObject)manifest["sha256"]!)
                if(Hash(File.ReadAllBytes(Path.Combine(root,pair.Key)))!=(string)pair.Value!)throw new InvalidOperationException("Input hash mismatch: "+pair.Key);
            var input=JObject.Parse(System.Text.Encoding.UTF8.GetString(bytes));
            var test=(JObject)((JArray)input["cases"]!).Single(x=>(string)x["case_id"]! == args[1]);
            if(!Enumerable.Range(4,8).Select(x=>"Q"+x.ToString("00")).Contains((string)test["fixture"]!))throw new InvalidOperationException("Out of scope");
            if(NetworkInterface.GetAllNetworkInterfaces().Any(x=>x.NetworkInterfaceType!=NetworkInterfaceType.Loopback))throw new InvalidOperationException("Network not denied");
            string socketResult;
            using(var socket=new Socket(AddressFamily.InterNetwork,SocketType.Stream,ProtocolType.Tcp))
            {
                try {socket.Connect(new IPEndPoint(IPAddress.Parse("203.0.113.1"),9));throw new InvalidOperationException("Network sentinel connected");}
                catch(SocketException e)when(e.SocketErrorCode==SocketError.NetworkUnreachable){socketResult=e.SocketErrorCode.ToString();}
            }
            output["network_denied"]=new JObject{["non_loopback_interfaces"]=0,["testnet_socket_result"]=socketResult};
            output["case_id"]=args[1];output["input_sha256"]=Hash(bytes);output["fixture_manifest_sha256"]=Hash(manifestBytes);
            Config.Set("data-folder","/work/source/Data");Config.Set("live-mode","false");
            Config.Set("results-destination-folder","/tmp/lean-results");
            Config.Set("log-handler","QuantConnect.Logging.ConsoleLogHandler");
            Config.Set("composer-dll-directory","/work/host/bin/Release/net10.0");
            var a=new IdentityAlgorithm(input,test);
            var hours=MarketHoursDatabase.FromDataFolder();var permissions=new DataPermissionManager();
            var service=new SecurityService(a.Portfolio.CashBook,hours,SymbolPropertiesDatabase.FromDataFolder(),a,
                RegisteredSecurityDataTypesProvider.Null,new SecurityCacheProvider(a.Portfolio),algorithm:a);
            a.Securities.SetSecurityService(service);
            var selection=new UniverseSelection(a,service,permissions,new DefaultDataProvider());
            var manager=new DataManager(new FixtureFeed(a),selection,a,a.TimeKeeper,hours,false,RegisteredSecurityDataTypesProvider.Null,permissions);
            a.SubscriptionManager.SetDataManager(manager);a.Initialize();a.OnEndOfTimeStep();a.SetFinishedWarmingUp();
            var results=new LocalResults();
            var job=new BacktestNodePacket{BacktestId="identity-time-fixture",Language=Language.CSharp,PeriodStart=a.StartDate,PeriodFinish=a.EndDate};
            using var brokerage=new BacktestingBrokerage(a);
            var transaction=new BacktestingTransactionHandler();a.Transactions.SetOrderProcessor(transaction);transaction.Initialize(a,brokerage,results);a.Transaction=transaction;
            var engine=new AlgorithmManager(false,job);var realtime=new BacktestingRealTimeHandler();
            realtime.Setup(a,job,results,null,engine.TimeLimit);a.Schedule.SetEventSchedule(realtime);a.SetStatus(AlgorithmStatus.Running);a.SetLocked();
            try
            {
                engine.Run(job,a,new FixtureStream(a,manager,selection),transaction,results,realtime,new LocalLeanManager(),new CancellationTokenSource(),new PerformanceTrackingTool());
                if(a.RunTimeError!=null)throw new InvalidOperationException("Native algorithm error",a.RunTimeError);
                if(!a.EndObserved)throw new InvalidOperationException("Native end not reached");
                output["business"]=a.Business();output["engine_status"]=a.Status.ToString();output["native_end_observed"]=a.EndObserved;
                output["native_orders"]=JArray.FromObject(transaction.OrderEvents.Select(e=>new{order_id=e.OrderId,sid=e.Symbol.ID.ToString(),status=e.Status.ToString(),quantity=Num(e.FillQuantity),price=Num(e.FillPrice),fee=Num(e.OrderFee.Value.Amount),utc=e.UtcTime.ToString("O")}));
                output["crosswalk"]=a.Crosswalk;output["envelope_journal"]=a.Journal;
                output["execution_complete"]=true;
            }
            finally{transaction.Exit();realtime.Exit();manager.RemoveAllSubscriptions();}
        }
        catch(Exception e){output["execution_complete"]=false;output["technical_error"]=e.ToString();}
        if(args.Length==3)File.WriteAllText(args[2],output.ToString(Formatting.None)+"\n");
        return (bool?)output["execution_complete"]==true?0:3;
    }
}

public sealed class LocalResults:BacktestingResultHandler
{
    public override void Sample(DateTime time){}
    public override void ProcessSynchronousEvents(bool forceProcess=false){}
    public override void SendStatusUpdate(AlgorithmStatus status,string message=""){}
    public override void OnSecuritiesChanged(SecurityChanges changes){}
    public override void OnWarmupFinished(){}
}

public sealed class IdentityAlgorithm:QCAlgorithm
{
    public readonly JObject Input,Case;
    public readonly Dictionary<string,Symbol> Symbols=new(StringComparer.Ordinal);
    public readonly JArray Crosswalk=new(),Journal=new(),RawMarks=new();
    public readonly List<long> Frames;
    public BacktestingTransactionHandler Transaction;
    public bool EndObserved,Admitted,Conflict;
    public string Reason;
    public JObject FillRecord,Current;
    public long Now;
    public string Routed="I1",MarketStatus;
    readonly List<JObject> pending;
    readonly Dictionary<string,string> seen=new(StringComparer.Ordinal);
    readonly List<string> orderStatuses=new();
    bool seeded,decided,finished;
    string initialAverage;
    OrderTicket ticket;
    public long Decision=>Program.Ns(Case["decision_ns"]!);
    public string Group=>(string)Case["fixture"]!;
    public IdentityAlgorithm(JObject input,JObject test)
    {
        Input=input;Case=test;MarketStatus=(string)test["status"]!;
        foreach(var row in (JArray)input["identities"]!)
        {
            var id=(string)row["instrument"]!;
            var symbol=new Symbol(SecurityIdentifier.GenerateEquity(DateTime.Parse((string)row["engine_date"]!,CultureInfo.InvariantCulture),
                (string)row["ticker"]!,Market.USA),(string)row["ticker"]!);
            Symbols.Add(id,symbol);
            var record=(JObject)row.DeepClone();record["engine_sid"]=symbol.ID.ToString();Crosswalk.Add(record);
        }
        if(Symbols.Values.Select(x=>x.ID).Distinct().Count()!=3)throw new InvalidOperationException("SID collision");
        pending=((JArray)test["events"]!).Cast<JObject>().OrderBy(x=>Program.Ns(x["available_ns"]!))
            .ThenBy(x=>(int)x["sequence"]!).ThenBy(x=>(string)x["id"]!,StringComparer.Ordinal).ToList();
        // Every source envelope is retained; DateTime is only a ceiling dispatch label.
        Frames=new[]{Program.Ceiling(Decision-1_000_000_000),Program.Ceiling(Decision),checked(Program.Ceiling(Decision+5_000_000_000)+100)}
            .Concat(pending.Select(x=>Program.Ceiling(Program.Ns(x["available_ns"]!))))
            .Where(x=>x>=Program.Ceiling(Decision-1_000_000_000)).Distinct().OrderBy(x=>x).ToList();
    }
    public override void Initialize()
    {
        var date=Program.Time(Decision);SetStartDate(date.Date);SetEndDate(date.Date);SetTimeZone(TimeZones.NewYork);SetCash(10000m);SetBenchmark(t=>0m);
        SetDateTime(Program.Time(Frames[0]));
        foreach(var pair in Symbols)
        {
            var security=AddSecurity(pair.Value,Resolution.Minute,fillForward:false,dataNormalizationMode:DataNormalizationMode.Raw);
            security.SetFillModel(new QuoteOnlyFill(this));security.SetFeeModel(new ConstantFeeModel(1));
            security.SetSlippageModel(new QuantConnect.Orders.Slippage.ConstantSlippageModel(0));
        }
    }
    public override void OnData(Slice slice)
    {
        if(!seeded)
        {
            foreach(var pair in Symbols)
                Securities[pair.Value].SetMarketPrice(new TradeBar(Program.Time(Decision-1_000_000_000).ConvertFromUtc(TimeZones.NewYork),pair.Value,100m,100m,100m,100m,0m,TimeSpan.Zero));
            Securities[Symbols["I1"]].Holdings.SetHoldings(100m,decimal.Parse((string)Case["seed_quantity"]!,CultureInfo.InvariantCulture));
            seeded=true;
            initialAverage=Program.Num(Securities[Symbols["I1"]].Holdings.AveragePrice);
            if(Group=="Q11" && (string)Case["normalization"]! == "Raw")RawMarks.Add(Program.Num(Securities[Symbols["I1"]].Price));
        }
    }
    public void Step(long dispatch)
    {
        // The initial user-universe slice creates subscriptions; its seed arrives on
        // the next native slice. No contract decision may precede that seed.
        if(!seeded && dispatch<Program.Ceiling(Decision))return;
        if(!seeded)throw new InvalidOperationException("Native seed not consumed at decision");
        if(!decided && dispatch>=Program.Ceiling(Decision))Decide();
        while(pending.Count>0 && Program.Ceiling(Program.Ns(pending[0]["available_ns"]!))<=dispatch)
        {
            var first=pending[0];
            // Same causal key has no ordering authority from physical file order.
            var group=pending.TakeWhile(e=>Program.Ns(e["available_ns"]!)==Program.Ns(first["available_ns"]!) &&
                (int)e["sequence"]! == (int)first["sequence"]! && (string)e["id"]! == (string)first["id"]!).ToList();
            if(group.Select(e=>e.ToString(Formatting.None)).Distinct(StringComparer.Ordinal).Count()>1)
            {
                Conflict=true;Reason="CONFLICT";Journal.Add(new JObject{["id"]=first["id"]!.DeepClone(),["result"]="CONFLICT",["available_ns"]=first["available_ns"]!.DeepClone(),["dispatch_ns"]=dispatch});
                pending.Clear();if(ticket!=null && FillRecord==null){ticket.Cancel("conflicting evidence abort");Transaction.ProcessSynchronousEvents();}break;
            }
            var e=pending[0];pending.RemoveAt(0);Now=Program.Ns(e["available_ns"]!);
            var id=(string)e["id"]!;var bytes=e.ToString(Formatting.None);
            if(seen.TryGetValue(id,out var prior))
            {
                Journal.Add(new JObject{["id"]=id,["result"]=prior==bytes?"DUPLICATE":"CONFLICT",["available_ns"]=Now,["dispatch_ns"]=dispatch});
                if(prior!=bytes){Conflict=true;Reason="CONFLICT";pending.Clear();break;}
                continue;
            }
            seen.Add(id,bytes);
            var kind=(string)e["kind"]!;
            Journal.Add(new JObject{["id"]=id,["kind"]=kind,["event_ns"]=e["event_ns"]!.DeepClone(),["available_ns"]=Now,
                ["receipt_ns"]=e["receipt_ns"]!.DeepClone(),["sequence"]=e["sequence"]!.DeepClone(),["dispatch_ns"]=dispatch,
                ["sha256"]=Program.Hash(System.Text.Encoding.UTF8.GetBytes(bytes))});
            if(kind=="halt")MarketStatus="HALTED";
            Current=null;
            if(kind=="quote")
            {
                if(TryDecimal(e["bid"],out var bid)&&TryDecimal(e["ask"],out var ask))
                {
                    var symbol=Symbols[(string)e["instrument"]!];
                    var tick=new Tick{Symbol=symbol,Time=Program.Time(Program.Ns(e["event_ns"]!)).ConvertFromUtc(TimeZones.NewYork),TickType=TickType.Quote,BidPrice=bid,AskPrice=ask,BidSize=1m,AskSize=1m};
                    Securities[symbol].SetMarketPrice(tick);
                    if(Group=="Q11" && id=="post_raw" && (string)Case["normalization"]! == "Raw")RawMarks.Add(Program.Num(Securities[symbol].BidPrice));
                }
                Current=e;
            }
            Transaction.ProcessSynchronousEvents();Current=null;
            if(dispatch<Program.Ceiling(Now))throw new InvalidOperationException("Early dispatch");
        }
        if(!finished && dispatch>Program.Ceiling(Decision+5_000_000_000))
        {
            finished=true;
            if(Admitted && FillRecord==null && !Conflict)
            {
                Reason ??="NO_VALID_QUOTE";
                ticket.Cancel("fixture deadline");Transaction.ProcessSynchronousEvents();
            }
        }
    }
    void Decide()
    {
        decided=true;Now=Decision;
        if((string)Case["normalization"]! != "Raw"){Reason="NORMALIZATION";return;}
        if(Group=="Q04")
        {
            var matches=((JArray)Case["identities"]!).Where(x=>(string)x["ticker"]! == "AAA" && Program.Ns(x["start_ns"]!)<=Decision && Decision<Program.Ns(x["end_ns"]!)).ToList();
            if(matches.Count!=1){Reason="IDENTITY_UNRESOLVED";return;}
            Routed=(string)matches[0]["instrument"]!;
        }
        var structural=Case["structural"];
        if(structural is JObject s && ((string)s["resolution"]! != "exact_interval" || (bool?)s["conflicting_class"]==true)){Reason="IDENTITY_UNRESOLVED";return;}
        if((string)Case["decision_quote"]!["instrument"]! != Routed){Reason="IDENTITY_UNRESOLVED";return;}
        Reason=Validate((JObject)Case["decision_quote"]!,Decision);
        if(Reason!=null)return;
        Admitted=true;
        ticket=MarketOrder(Symbols[Routed],decimal.Parse((string)Case["quantity"]!,CultureInfo.InvariantCulture),asynchronous:true,tag:"frozen fixture intent");
        if(ticket.GetMostRecentOrderResponse().IsError)throw new InvalidOperationException("Native intent rejected: "+ticket.GetMostRecentOrderResponse());
        Transaction.ProcessSynchronousEvents();
    }
    public static bool TryDecimal(JToken x,out decimal v)=>decimal.TryParse((string)x,NumberStyles.Number,CultureInfo.InvariantCulture,out v);
    public string Validate(JObject q,long now)
    {
        if(Program.Ns(q["available_ns"]!)>now || (q["receipt_ns"]!.Type!=JTokenType.Null && Program.Ns(q["receipt_ns"]!)>now))return "UNAVAILABLE";
        var age=now-Program.Ns(q["event_ns"]!);if(age<0 || age>2_000_000_000)return "STALE";
        if(!TryDecimal(q["bid"],out var bid)||!TryDecimal(q["ask"],out var ask)||bid<=0 || ask<=bid)return "MALFORMED_PRICE";
        if(10000m*(ask-bid)>20m*(ask+bid)/2m)return "SPREAD";
        if(q["conditions"] is not JArray conditions || conditions.Count!=1 || (string)conditions[0]! != "R")return "CONDITION";
        if(MarketStatus!="TRADABLE")return "STATUS_UNKNOWN";
        if((bool)q["gap"]!)return "GAP";
        if((string)q["normalization"]! != "Raw")return "NORMALIZATION";
        if(!TryDecimal(q["size"],out var size) || size<=0)return "SIZE";
        if((string)q["unit"]! == "round_lot")
        {
            if(!TryDecimal(q["factor"],out var factor)||factor<=0||q["unit_evidence"]!.Type==JTokenType.Null)return "SIZE_UNIT";
        }
        else if((string)q["unit"]! != "shares")return "SIZE_UNIT";
        return null;
    }
    public override void OnOrderEvent(OrderEvent e)
    {
        orderStatuses.Add(e.Status.ToString());
        if(e.Status==OrderStatus.Filled && (e.FillQuantity!=decimal.Parse((string)Case["quantity"]!,CultureInfo.InvariantCulture) || e.OrderFee.Value.Amount!=1m))
            throw new InvalidOperationException("Native fill/fee mismatch");
    }
    public override void OnEndOfAlgorithm(){EndObserved=true;}
    public JObject Business()
    {
        var receipt=Case["decision_quote"]!["receipt_ns"]!;
        var b=new JObject{["admitted"]=Admitted,["reason"]=Reason,["fill"]=FillRecord,
            ["cash"]=Program.Num(Portfolio.CashBook["USD"].Amount),["quantity"]=Program.Num(Symbols.Values.Sum(x=>Securities[x].Holdings.Quantity)),
            ["native_order_statuses"]=JArray.FromObject(orderStatuses),["decision_receipt_ns"]=receipt.DeepClone(),
            ["clock_mode"]=receipt.Type==JTokenType.Null?"simulated_historical":"prospective",["routes"]=new JArray(),
            ["structural"]=Group=="Q05"?Case["structural"]!.DeepClone():null,["raw_marks"]=RawMarks};
        b["contract_state"]=Conflict?"ABORTED_CONFLICT":"COMPLETE";
        b["positions"]=JObject.FromObject(Symbols.ToDictionary(x=>x.Key,x=>Program.Num(Securities[x.Value].Holdings.Quantity)));
        b["initial_average"]=initialAverage;
        if(Group=="Q04")
        {
            b["routes"]=Admitted?new JArray(Routed):new JArray();b["held_identity"]="I1";b["class_separate"]=Symbols["I1"]!=Symbols["I3"];
            b["held_quantity"]=Program.Num(Securities[Symbols["I1"]].Holdings.Quantity-(Routed=="I1"&&FillRecord!=null?decimal.Parse((string)Case["quantity"]!,CultureInfo.InvariantCulture):0));
        }
        return b;
    }
}

public sealed class QuoteOnlyFill:FillModel
{
    readonly IdentityAlgorithm a;
    public QuoteOnlyFill(IdentityAlgorithm algorithm){a=algorithm;}
    public override OrderEvent MarketFill(Security security,MarketOrder order)
    {
        var fill=new OrderEvent(order,a.UtcTime,OrderFee.Zero);
        var q=a.Current;
        if(q==null || a.FillRecord!=null || !a.Admitted || a.Conflict)return fill;
        if((string)q["instrument"]! != a.Routed || a.Now<a.Decision+1_000_000_000 || a.Now>a.Decision+5_000_000_000 || a.Validate(q,a.Now)!=null)return fill;
        if(a.Group=="Q04" && !((JArray)a.Case["identities"]!).Any(r=>(string)r["instrument"]! == a.Routed && Program.Ns(r["start_ns"]!)<=a.Now && a.Now<Program.Ns(r["end_ns"]!)))return fill;
        var size=decimal.Parse((string)q["size"]!,CultureInfo.InvariantCulture);
        if((string)q["unit"]! == "round_lot")size*=decimal.Parse((string)q["factor"]!,CultureInfo.InvariantCulture);
        if(order.Quantity>size*0.1m){a.Reason="CAPACITY";return fill;}
        var ask=decimal.Parse((string)q["ask"]!,CultureInfo.InvariantCulture);
        if(security.AskPrice!=ask)throw new InvalidOperationException("Native quote projection mismatch");
        fill.Status=OrderStatus.Filled;fill.FillQuantity=order.Quantity;fill.FillPrice=security.AskPrice*1.0005m;
        a.FillRecord=new JObject{["quote_id"]=q["id"]!.DeepClone(),["instrument"]=a.Routed,["event_ns"]=q["event_ns"]!.DeepClone(),
            ["available_ns"]=q["available_ns"]!.DeepClone(),["receipt_ns"]=q["receipt_ns"]!.DeepClone(),
            ["dispatch_ns"]=Program.Ceiling(a.Now),["quantity"]=Program.Num(order.Quantity),["price"]=Program.Num(fill.FillPrice),["fee"]="1"};
        a.FillRecord["evidence"]=q["evidence"]!.DeepClone();a.FillRecord["source"]=q["source"]!.DeepClone();a.FillRecord["tape"]=q["tape"]!.DeepClone();
        a.FillRecord["precision"]="nanosecond";a.FillRecord["clock_mode"]=q["receipt_ns"]!.Type==JTokenType.Null?"simulated_historical":"prospective";
        return fill;
    }
}

// Pacing/HasData TradeBars are explicitly synthetic; QuoteOnlyFill never reads them.
public sealed class FixtureFeed:IDataFeed
{
    readonly IdentityAlgorithm a;public FixtureFeed(IdentityAlgorithm algorithm){a=algorithm;}
    public bool IsActive=>true;
    public void Initialize(IAlgorithm a,AlgorithmNodePacket j,IResultHandler r,IMapFileProvider m,IFactorFileProvider f,IDataProvider p,IDataFeedSubscriptionManager s,IDataFeedTimeProvider t,IDataChannelProvider c){}
    public Subscription CreateSubscription(SubscriptionRequest request)
    {
        var points=new List<SubscriptionData>();
        if(request.IsUniverseSubscription)
        {
            var start=a.UtcTime;
            points.Add(new SubscriptionData(new BaseDataCollection(start.ConvertFromUtc(TimeZones.NewYork),request.Configuration.Symbol,Array.Empty<BaseData>()),start));
        }
        else if(request.Configuration.Symbol==a.Symbols["I1"])
            foreach(var ns in a.Frames)
            {
                var utc=Program.Time(ns);
                var data=new TradeBar(utc.ConvertFromUtc(TimeZones.NewYork),request.Configuration.Symbol,100m,100m,100m,100m,0m,TimeSpan.Zero);
                points.Add(new SubscriptionData(data,utc));
            }
        var offsets=new TimeZoneOffsetProvider(request.Configuration.ExchangeTimeZone,request.StartTimeUtc,request.EndTimeUtc);
        return new Subscription(request,points.GetEnumerator(),offsets);
    }
    public void RemoveSubscription(Subscription subscription){}
    public void Exit(){}
}
public sealed class FrozenClock:ITimeProvider{public DateTime Time;public DateTime GetUtcNow()=>Time;}
public sealed class FixtureStream:ISynchronizer
{
    readonly IdentityAlgorithm a;readonly DataManager manager;readonly UniverseSelection selection;
    public FixtureStream(IdentityAlgorithm algorithm,DataManager m,UniverseSelection s){a=algorithm;manager=m;selection=s;}
    public IEnumerable<TimeSlice> StreamData(CancellationToken token)
    {
        var clock=new FrozenClock{Time=Program.Time(a.Frames[0])};var sync=new SubscriptionSynchronizer(selection,new PerformanceTrackingTool());
        sync.SetTimeProvider(clock);sync.SetTimeSliceFactory(new TimeSliceFactory(a.TimeZone));
        sync.SubscriptionFinished+=(sender,sub)=>manager.RemoveSubscription(sub.Configuration);
        using var stream=sync.Sync(manager.DataFeedSubscriptions,token).GetEnumerator();
        foreach(var ns in a.Frames)
        {
            clock.Time=Program.Time(ns);
            do{if(!stream.MoveNext())throw new InvalidOperationException("Native synchronizer ended early");yield return stream.Current;}while(stream.Current.IsTimePulse);
            a.Step(ns);
            if(a.Conflict)yield break;
        }
    }
}
