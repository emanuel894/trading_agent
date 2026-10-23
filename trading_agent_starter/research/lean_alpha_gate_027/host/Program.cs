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
using QuantConnect.Configuration;
using QuantConnect.Data;
using QuantConnect.Data.Auxiliary;
using QuantConnect.Data.Market;
using QuantConnect.Data.UniverseSelection;
using QuantConnect.Interfaces;
using QuantConnect.Lean.Engine;
using QuantConnect.Lean.Engine.DataFeeds;
using QuantConnect.Lean.Engine.HistoricalData;
using QuantConnect.Lean.Engine.RealTime;
using QuantConnect.Lean.Engine.Results;
using QuantConnect.Lean.Engine.Server;
using QuantConnect.Lean.Engine.TransactionHandlers;
using QuantConnect.Orders;
using QuantConnect.Packets;
using QuantConnect.Securities;
using QuantConnect.Util;

public sealed class OfflineViolation:Exception{public string Code;public OfflineViolation(string code):base(code){Code=code;}}
public static class Program
{
 public const string Pin="d4cac37514427c84d40064cecbf3f0e6be4b0137";
 public static string Num(decimal x)=>x.ToString("G29",CultureInfo.InvariantCulture);
 public static decimal Dec(JToken x)=>decimal.Parse((string)x!,CultureInfo.InvariantCulture);
 public static string Hash(byte[] x)=>Convert.ToHexStringLower(SHA256.HashData(x));
 public static long Ceiling(long n)=>checked(((n+99)/100)*100);
 public static DateTime Time(long n)=>DateTime.UnixEpoch.AddTicks(Ceiling(n)/100);
 public static int Main(string[] args)
 {
  var o=new JObject{["source_pin"]=Pin,["case_complete"]=false,["execution_complete"]=false};
  var guard=new OfflineData();ResearchAlgorithm active=null;
  try
  {
   if(args.Length!=4)throw new ArgumentException("control fixtures, case ID, output, data store required");
   var bytes=File.ReadAllBytes(Path.Combine(args[0],"input.json"));var mb=File.ReadAllBytes(Path.Combine(args[0],"manifest.json"));
   var control=JObject.Parse(System.Text.Encoding.UTF8.GetString(bytes));var test=(JObject)((JArray)control["cases"]!).Single(c=>(string)c["case_id"]! ==args[1]);
   o["case_id"]=args[1];o["input_sha256"]=Hash(bytes);o["fixture_manifest_sha256"]=Hash(mb);
   if(!new[]{"Q21","Q22","Q23","Q24","Q25","Q26","Q32","Q33"}.Contains((string)test["fixture"]!))throw new InvalidOperationException("Out of scope");
   if(NetworkInterface.GetAllNetworkInterfaces().Any(n=>n.NetworkInterfaceType!=NetworkInterfaceType.Loopback))throw new InvalidOperationException("Network not denied");
   using(var socket=new Socket(AddressFamily.InterNetwork,SocketType.Stream,ProtocolType.Tcp))
   {
    try{socket.Connect(new IPEndPoint(IPAddress.Parse("203.0.113.1"),9));throw new InvalidOperationException("Network sentinel connected");}
    catch(SocketException e)when(e.SocketErrorCode==SocketError.NetworkUnreachable){o["network_denied"]=new JObject{["non_loopback_interfaces"]=0,["testnet_socket_result"]=e.SocketErrorCode.ToString()};}
   }
   var store=args[3];if(!Directory.Exists(store)||!Directory.EnumerateFiles(store).Any())throw new OfflineViolation("EMPTY_STORE");
   foreach(var entry in (JObject)JObject.Parse(System.Text.Encoding.UTF8.GetString(mb))["sha256"]!)
   {
    var path=Path.Combine(store,entry.Key);if(!File.Exists(path))throw new OfflineViolation("MISSING_INPUT");
    if(Hash(File.ReadAllBytes(path))!=(string)entry.Value!)throw new OfflineViolation("HASH_MISMATCH");
   }
   // The manifest is trusted by the runner's reviewed binding, never supplied by the mutable store.
   var config=JObject.Parse(File.ReadAllText(Path.Combine(store,"config.json")));
   foreach(var name in new[]{"trading_enabled","allow_paper_orders","alpaca_live_trade"})if((bool)config[name]!)throw new InvalidOperationException("Trading enabled");
   var admitted=JObject.Parse(File.ReadAllText(Path.Combine(store,"input.json")));
   test=(JObject)((JArray)admitted["cases"]!).Single(c=>(string)c["case_id"]! ==args[1]);
   Config.Set("data-folder","/work/source/Data");Config.Set("live-mode","false");Config.Set("results-destination-folder","/tmp/results");Config.Set("composer-dll-directory","/packet/host/bin/Release/net10.0");
   if((string)test["fixture"]! =="Q33")
   {
    var arms=new JObject();var native=new JObject();JObject outcome=null;
    if((string)test["arm_mode"]! =="unresolved")
    {
     var reference=(JObject)test["reused_claim"]!;var path=Path.GetFullPath(Path.Combine("/prior",((string)reference["path"]!)[3..]));
     if(!path.StartsWith("/prior/lean_terminal_017/evidence/",StringComparison.Ordinal))throw new InvalidOperationException("Claim path escape");
     var claimBytes=File.ReadAllBytes(path);if(Hash(claimBytes)!=(string)reference["sha256"]!)throw new InvalidOperationException("Prior claim binding changed");
     var prior=JObject.Parse(System.Text.Encoding.UTF8.GetString(claimBytes));outcome=(JObject)((JArray)prior["snapshots"]!).Last!;
     if((bool)prior["execution_complete"]! !=true||(string)outcome["engine_quantity"]! !="10"||(string)outcome["cash"]! !="9000")throw new InvalidOperationException("Prior claim evidence invalid");
    }
    foreach(var arm in new[]{"A","B","C","N"})
    {
     active=new ResearchAlgorithm(test);var result=Run(active,guard);
     arms[arm]=new JObject{["accounting"]=active.Business(),["diagnostics"]=new JObject{["equity"]=arm=="C"?"999999":"-23",["sharpe"]=arm=="N"?"999":"-999"}};native[arm]=result;
    }
    o["business"]=new JObject{["arms"]=arms,["reused_outcome"]=outcome};o["native"]=native;
   }
   else{active=new ResearchAlgorithm(test);o["native"]=Run(active,guard);o["business"]=active.Business();}
   o["provider_calls"]=guard.Calls;o["case_complete"]=true;o["execution_complete"]=true;
  }
  catch(OfflineViolation e)
  {
   o["guard_error"]=e.Code;o["business"]=null;o["provider_calls"]=guard.Calls;o["native_submissions"]=active?.GateCalls??0;o["case_complete"]=true;
  }
  catch(Exception e){o["technical_error"]=e.ToString();}
  if(args.Length>=3)File.WriteAllText(args[2],o.ToString(Formatting.None)+"\n");
  return (bool)o["case_complete"]!?0:3;
 }
 static JObject Run(ResearchAlgorithm a,OfflineData guard)
 {
  var hours=MarketHoursDatabase.FromDataFolder();var permissions=new DataPermissionManager();
  if((string)a.Case["fixture"]! =="Q24")
  {
   // The matrix's synthetic sessions are authoritative, including Jan9. Never substitute today's provider calendar.
   var schedule=(JObject)((JArray)a.Case["steps"]!).First(s=>(string)s["op"]! =="schedule");
   var closes=((JArray)schedule["closes_ns"]!).Select(n=>Time((long)n).ConvertFromUtc(TimeZones.NewYork)).ToArray();
   var dates=closes.Select(n=>n.Date).ToHashSet();var holidays=new List<DateTime>();for(var d=closes.First().Date;d<=closes.Last().Date;d=d.AddDays(1))if(!dates.Contains(d))holidays.Add(d);
   var original=hours.GetEntry(Market.USA,a.Symbols["I1"].Value,SecurityType.Equity).ExchangeHours;
   var projected=new SecurityExchangeHours(TimeZones.NewYork,holidays,original.MarketHours.ToDictionary(p=>p.Key,p=>p.Value),closes.Where(n=>n.TimeOfDay<TimeSpan.FromHours(16)).ToDictionary(n=>n.Date,n=>n.TimeOfDay),new Dictionary<DateTime,TimeSpan>());
   foreach(var symbol in a.Symbols.Values)hours.SetEntry(Market.USA,symbol.Value,SecurityType.Equity,projected,TimeZones.NewYork);
  }
  var service=new SecurityService(a.Portfolio.CashBook,hours,SymbolPropertiesDatabase.FromDataFolder(),a,RegisteredSecurityDataTypesProvider.Null,new SecurityCacheProvider(a.Portfolio),algorithm:a);a.Securities.SetSecurityService(service);
  var selection=new UniverseSelection(a,service,permissions,guard);var manager=new DataManager(new FixtureFeed(a),selection,a,a.TimeKeeper,hours,false,RegisteredSecurityDataTypesProvider.Null,permissions);
  a.SubscriptionManager.SetDataManager(manager);a.Initialize();a.OnEndOfTimeStep();a.SetFinishedWarmingUp();
  var result=new LocalResults();var job=new BacktestNodePacket{BacktestId="issue27-synthetic",Language=Language.CSharp,PeriodStart=a.StartDate,PeriodFinish=a.EndDate};
  using var brokerage=new LocalBrokerage(a);a.Brokerage=brokerage;var transaction=new BacktestingTransactionHandler();a.Transactions.SetOrderProcessor(transaction);transaction.Initialize(a,brokerage,result);a.Transaction=transaction;
  var engine=new AlgorithmManager(false,job);var realtime=new BacktestingRealTimeHandler();realtime.Setup(a,job,result,null,engine.TimeLimit);a.Schedule.SetEventSchedule(realtime);a.SetStatus(AlgorithmStatus.Running);a.SetLocked();
  try
  {
   if((string)a.Case["ingress"]=="download")
   {
    a.SetApi(new OfflineApi(guard));try{a.Download("https://example.invalid/forbidden-default-data");}finally{guard.Check();}
   }
   if((string)a.Case["ingress"]=="history")
   {
    var map=new LocalDiskMapFileProvider();map.Initialize(guard);var factor=new LocalDiskFactorFileProvider();factor.Initialize(map,guard);
    using var cache=new SingleEntryDataCacheProvider(guard);var history=new SubscriptionDataReaderHistoryProvider();
    history.Initialize(new HistoryProviderInitializeParameters(job,null,guard,cache,map,factor,null,false,permissions,null,a.Settings));a.HistoryProvider=history;
    try{a.History<TradeBar>(a.Symbols["I1"],new DateTime(2025,1,2),new DateTime(2025,1,3),Resolution.Minute).ToList();}finally{guard.Check();}
    throw new InvalidOperationException("History did not reach provider guard");
   }
   engine.Run(job,a,new FixtureStream(a,manager,selection),transaction,result,realtime,new LocalLeanManager(),new CancellationTokenSource(),new PerformanceTrackingTool());
   if(a.RunTimeError!=null)throw new InvalidOperationException("Native algorithm error",a.RunTimeError);if(!a.EndObserved)throw new InvalidOperationException("Native end missing");guard.Check();
   var orders=new JArray(transaction.OrderEvents.Select(e=>new JObject{["order_id"]=e.OrderId,["intent"]=a.IntentFor(e.OrderId),["instrument"]=a.Instrument(e.Symbol),["sid"]=e.Symbol.ID.ToString(),["status"]=e.Status.ToString(),["quantity"]=Num(e.FillQuantity),["price"]=Num(e.FillPrice),["fee"]=Num(e.OrderFee.Value.Amount),["native_dispatch_ns"]=(e.UtcTime.Ticks-DateTime.UnixEpoch.Ticks)*100}));
   return new JObject{["end_observed"]=a.EndObserved,["status"]=a.Status.ToString(),["cash"]=Num(a.Portfolio.CashBook["USD"].Amount),["quantities"]=new JObject(a.Symbols.Select(p=>new JProperty(p.Key,Num(a.Securities[p.Value].Holdings.Quantity)))),["crosswalk"]=new JObject(a.Symbols.Select(p=>new JProperty(p.Key,p.Value.ID.ToString()))),["events"]=orders,["gate_calls"]=a.GateCalls,["open_orders"]=a.Transactions.GetOpenOrders().Count};
  }
  finally{transaction.Exit();realtime.Exit();manager.RemoveAllSubscriptions();}
 }
}
// Every undeclared native data request is sticky-fatal, including exceptions swallowed by a reader.
public sealed class OfflineData:IDataProvider
{
 public int Calls;public bool Denied;public event EventHandler<DataProviderNewDataRequestEventArgs> NewDataRequest;
 public Stream Fetch(string key){if(!Denied)Calls++;Denied=true;throw new OfflineViolation("PROVIDER_DENIED");}
 public void Check(){if(Denied)throw new OfflineViolation("PROVIDER_DENIED");}
}
public sealed class OfflineApi:QuantConnect.Api.Api
{
 readonly OfflineData guard;public OfflineApi(OfflineData g){guard=g;}
 public override string Download(string address,IEnumerable<KeyValuePair<string,string>> headers,string userName,string password){guard.Fetch(address);throw new InvalidOperationException("Unreachable");}
}
public sealed class LocalResults:BacktestingResultHandler
{
 public override void Sample(DateTime time){}public override void ProcessSynchronousEvents(bool forceProcess=false){}public override void SendStatusUpdate(AlgorithmStatus status,string message=""){}public override void OnSecuritiesChanged(SecurityChanges changes){}public override void OnWarmupFinished(){}
}
public sealed class FixtureFeed:IDataFeed
{
 readonly ResearchAlgorithm a;public FixtureFeed(ResearchAlgorithm x){a=x;}public bool IsActive=>true;
 public void Initialize(IAlgorithm a,AlgorithmNodePacket j,IResultHandler r,IMapFileProvider m,IFactorFileProvider f,IDataProvider p,IDataFeedSubscriptionManager s,IDataFeedTimeProvider t,IDataChannelProvider c){}
 public Subscription CreateSubscription(SubscriptionRequest request)
 {
  var points=new List<SubscriptionData>();
  if(request.IsUniverseSubscription){var start=a.UtcTime;points.Add(new SubscriptionData(new BaseDataCollection(start.ConvertFromUtc(TimeZones.NewYork),request.Configuration.Symbol,Array.Empty<BaseData>()),start));}
  else if(request.Configuration.Symbol==a.Symbols["I1"])foreach(var ns in a.Frames)
  {
   var utc=Program.Time(ns);BaseData data;
   if(ns==a.Frames[0]){var price=Program.Dec(a.Case["mark"]!);data=new TradeBar(utc.ConvertFromUtc(TimeZones.NewYork),request.Configuration.Symbol,price,price,price,price,0m,TimeSpan.Zero);}
   else data=new ClockPulse{Symbol=request.Configuration.Symbol,Time=utc.ConvertFromUtc(TimeZones.NewYork),Value=0};
   points.Add(new SubscriptionData(data,utc));
  }
  return new Subscription(request,points.GetEnumerator(),new TimeZoneOffsetProvider(request.Configuration.ExchangeTimeZone,request.StartTimeUtc,request.EndTimeUtc));
 }
 public void RemoveSubscription(Subscription s){}public void Exit(){}
}
// Zero-valued Base data paces clocks without overwriting evidenced security marks.
public sealed class ClockPulse:BaseData{}
public sealed class FrozenClock:ITimeProvider{public DateTime Time;public DateTime GetUtcNow()=>Time;}
public sealed class FixtureStream:ISynchronizer
{
 readonly ResearchAlgorithm a;readonly DataManager manager;readonly UniverseSelection selection;
 public FixtureStream(ResearchAlgorithm x,DataManager m,UniverseSelection s){a=x;manager=m;selection=s;}
 public IEnumerable<TimeSlice> StreamData(CancellationToken token)
 {
  var clock=new FrozenClock{Time=Program.Time(a.Frames[0])};var sync=new SubscriptionSynchronizer(selection,new PerformanceTrackingTool());sync.SetTimeProvider(clock);sync.SetTimeSliceFactory(new TimeSliceFactory(a.TimeZone));sync.SubscriptionFinished+=(s,sub)=>manager.RemoveSubscription(sub.Configuration);
  using var stream=sync.Sync(manager.DataFeedSubscriptions,token).GetEnumerator();foreach(var ns in a.Frames){clock.Time=Program.Time(ns);do{if(!stream.MoveNext())throw new InvalidOperationException("Native synchronizer ended early");yield return stream.Current;}while(stream.Current.IsTimePulse);a.Step(ns);}
 }
}
