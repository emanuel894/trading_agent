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
            if(!Enumerable.Range(12,9).Select(x=>"Q"+x.ToString("00")).Contains((string)test["fixture"]!))throw new InvalidOperationException("Out of scope");
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
            Config.Set("composer-dll-directory","/stage/host/bin/Release/net10.0");
            var a=new StageAlgorithm(input,test);
            var hours=MarketHoursDatabase.FromDataFolder();var permissions=new DataPermissionManager();
            var service=new SecurityService(a.Portfolio.CashBook,hours,SymbolPropertiesDatabase.FromDataFolder(),a,
                RegisteredSecurityDataTypesProvider.Null,new SecurityCacheProvider(a.Portfolio),algorithm:a);
            a.Securities.SetSecurityService(service);
            var selection=new UniverseSelection(a,service,permissions,new DefaultDataProvider());
            var manager=new DataManager(new FixtureFeed(a),selection,a,a.TimeKeeper,hours,false,RegisteredSecurityDataTypesProvider.Null,permissions);
            a.SubscriptionManager.SetDataManager(manager);a.Initialize();a.OnEndOfTimeStep();a.SetFinishedWarmingUp();
            var results=new LocalResults();
            var job=new BacktestNodePacket{BacktestId="identity-time-fixture",Language=Language.CSharp,PeriodStart=a.StartDate,PeriodFinish=a.EndDate};
            using var brokerage=a.Scripted?new ScriptedBrokerage(a):(BacktestingBrokerage)new BacktestingBrokerage(a);a.Brokerage=brokerage;
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
                output["native_open_orders"]=a.Transactions.GetOpenOrders().Count;
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

// Pacing/HasData TradeBars are explicitly synthetic; QuoteOnlyFill never reads them.
public sealed class FixtureFeed:IDataFeed
{
    readonly StageAlgorithm a;public FixtureFeed(StageAlgorithm algorithm){a=algorithm;}
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
    readonly StageAlgorithm a;readonly DataManager manager;readonly UniverseSelection selection;
    public FixtureStream(StageAlgorithm algorithm,DataManager m,UniverseSelection s){a=algorithm;manager=m;selection=s;}
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
