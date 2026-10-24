// Diagnostic native lifecycle only. Original SIP rows remain non-executable custom data.
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Threading;
using System.Text;
using System.Security.Cryptography;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using QuantConnect;
using QuantConnect.Algorithm;
using QuantConnect.Brokerages;
using QuantConnect.Brokerages.Backtesting;
using QuantConnect.Configuration;
using QuantConnect.Data;
using QuantConnect.Data.Auxiliary;
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

namespace SipEngine
{
public static class Entry
{
 public static DateTime Time(long ns)=>DateTime.UnixEpoch.AddTicks(ns/100);
 public static long Ns(DateTime time)=>(time.Ticks-DateTime.UnixEpoch.Ticks)*100;
 public static string Hash(byte[] data)=>Convert.ToHexStringLower(SHA256.HashData(data));
 public static int Main(string[] args)
 {
  var result=new JObject{["initialized"]=false,["ended"]=false,["orders"]=0};
  Diagnostic active=null;
  try
  {
   if(args.Length!=3||File.Exists(args[1]))throw new InvalidOperationException("new output/input binding required");
   var bytes=File.ReadAllBytes(args[0]);if(bytes.Length>50*1024*1024||Hash(bytes)!=args[2])throw new InvalidOperationException("INPUT_BINDING");
   var input=JObject.Parse(Encoding.UTF8.GetString(bytes));
   if((string)input["version"]! !="SIP_NATIVE_OBSERVATION_ENGINE_V1" || (string)input["mode"]! !="OBSERVATION_ONLY" || (string)input["execution_policy"]! !="DENY_ALL" || (bool)input["historical_receipt_proven"]!)throw new InvalidOperationException("OBSERVATION_SCOPE");
   var batches=(JArray)input["batches"]!;if(batches.Count==0||batches.Count>50000)throw new InvalidOperationException("BATCH_CAP");
   long last=-1;int events=0;
   foreach(JObject batch in batches)
   {
    long at=(long)batch["native_ns"]!;if(at<=last||at%100!=0)throw new InvalidOperationException("BATCH_ORDER");last=at;
    var payload=(JArray)batch["payload"]!;
    if(payload.Count==0 || Hash(Encoding.UTF8.GetBytes(payload.ToString(Formatting.None)))!=(string)batch["payload_sha256"]!)throw new InvalidOperationException("PAYLOAD_BINDING");
    foreach(JObject e in payload)
    {
     var kind=(string)e["kind"]!;long source=(long)e["source_ns"]!;long emission=(long)e["emission_ns"]!;
     if((bool)e["execution_admitted"]! || (bool)e["availability_proven"]! || e["historical_received_at"]!.Type!=JTokenType.Null || (string)e["state"]! !="UNQUALIFIED" || (string)e["size_units"]! !="UNQUALIFIED_PROVIDER_NATIVE")throw new InvalidOperationException("EXECUTABLE_INPUT_FORBIDDEN");
     if((kind!="bars"&&kind!="quotes") || emission!=source+(kind=="bars"?60_000_000_000:0) || checked(((emission+99)/100)*100)!=at)throw new InvalidOperationException("EVENT_CLOCK");
     if(!((JArray)input["sessions"]!).Any(s=>(long)s["open_ns"]!<=source && (kind=="bars"?emission<=(long)s["close_ns"]!:emission<(long)s["close_ns"]!)))throw new InvalidOperationException("SESSION_BOUNDARY");
     events++;if(events>50000)throw new InvalidOperationException("EVENT_CAP");
    }
   }
   if(events!=(int)input["events"]!)throw new InvalidOperationException("EVENT_COUNT");
   Config.Set("data-folder","/runtime-data");Config.Set("live-mode","false");Config.Set("results-destination-folder","/tmp/results");Config.Set("composer-dll-directory","/tmp/app");
   var guard=new global::OfflineData();var algorithm=new Diagnostic(input);active=algorithm;
   Run(algorithm,guard);
   result=algorithm.Result();result["input_sha256"]=args[2];result["provider_calls"]=guard.Calls;guard.Check();
  }
  catch(Exception error){result["initialized"]=active?.Initialized??false;result["ended"]=active?.Ended??false;result["on_data_batches"]=active?.Received??0;result["events"]=active?.Events??0;result["error"]=error.ToString();}
  if(args.Length>=2){using var f=new FileStream(args[1],FileMode.CreateNew,FileAccess.Write);using var w=new StreamWriter(f);w.Write(result.ToString(Formatting.None)+"\n");}
  return result["error"]==null?0:3;
 }
 static void Run(Diagnostic a,global::OfflineData guard)
 {
  var hours=MarketHoursDatabase.FromDataFolder();var permissions=new DataPermissionManager();
  var service=new SecurityService(a.Portfolio.CashBook,hours,SymbolPropertiesDatabase.FromDataFolder(),a,RegisteredSecurityDataTypesProvider.Null,new SecurityCacheProvider(a.Portfolio),algorithm:a);a.Securities.SetSecurityService(service);
  var selection=new UniverseSelection(a,service,permissions,guard);var manager=new DataManager(new ObservationFeed(a),selection,a,a.TimeKeeper,hours,false,RegisteredSecurityDataTypesProvider.Null,permissions);a.SubscriptionManager.SetDataManager(manager);
  var map=new LocalDiskMapFileProvider();map.Initialize(guard);var factor=new LocalDiskFactorFileProvider();factor.Initialize(map,guard);
  using var cache=new SingleEntryDataCacheProvider(guard);var history=new SubscriptionDataReaderHistoryProvider();history.Initialize(new HistoryProviderInitializeParameters(null,null,guard,cache,map,factor,null,false,permissions,null,a.Settings));a.HistoryProvider=history;a.SetApi(new global::OfflineApi(guard));
  a.Initialize();a.OnEndOfTimeStep();a.SetFinishedWarmingUp();
  var result=new global::LocalResults();var job=new BacktestNodePacket{BacktestId="sip-observation-diagnostic",Language=Language.CSharp,PeriodStart=a.StartDate,PeriodFinish=a.EndDate};
  using var brokerage=new BacktestingBrokerage(a);var transaction=new BacktestingTransactionHandler();a.Transactions.SetOrderProcessor(transaction);transaction.Initialize(a,brokerage,result);
  var engine=new AlgorithmManager(false,job);var realtime=new BacktestingRealTimeHandler();realtime.Setup(a,job,result,null,engine.TimeLimit);a.Schedule.SetEventSchedule(realtime);a.SetStatus(AlgorithmStatus.Running);a.SetLocked();
  try
  {
   engine.Run(job,a,new ObservationStream(a,manager,selection),transaction,result,realtime,new LocalLeanManager(),new CancellationTokenSource(),new PerformanceTrackingTool());
   if(a.RunTimeError!=null)throw new InvalidOperationException("NATIVE_RUNTIME",a.RunTimeError);
   if(!a.Ended||a.Received!=a.Batches.Count||a.Events!=(int)a.Input["events"]!||a.Trace!=(string)a.Input["expected_trace_sha256"]!)throw new InvalidOperationException("DELIVERY_ORACLE");
   if(a.Transactions.GetOrders().Any()||a.Transactions.GetOpenOrders().Any()||transaction.OrderEvents.Any()||a.DeniedSubmissions!=0)throw new InvalidOperationException("ORDER_FORBIDDEN");
   guard.Check();
  }
  finally{transaction.Exit();realtime.Exit();manager.RemoveAllSubscriptions();}
 }
}
public sealed class ObservationBatch:BaseData
{
 public JArray Payload;public string PayloadHash;public int Index;public long NativeNs;
}
public sealed class Diagnostic:QCAlgorithm
{
 public readonly JObject Input;public readonly List<ObservationBatch> Batches=new();public readonly List<long> Frames;
 public Symbol StreamSymbol;public bool Initialized,Ended;public int Received,Events,BarEvents,QuoteEvents,DeniedSubmissions;public string Trace;
 readonly IncrementalHash trace=IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
 public Diagnostic(JObject input)
 {
  Input=input;int index=0;
  foreach(JObject b in (JArray)input["batches"]!)Batches.Add(new ObservationBatch{Payload=(JArray)b["payload"]!,PayloadHash=(string)b["payload_sha256"]!,Index=index++,NativeNs=(long)b["native_ns"]!,Time=Entry.Time((long)b["native_ns"]!),Value=0});
  Frames=new[]{Batches[0].NativeNs-2_000_000_000,Batches[0].NativeNs-1_000_000_000}.Concat(Batches.Select(b=>b.NativeNs)).Append(Batches.Last().NativeNs+100).ToList();
 }
 public override void Initialize()
 {
  SetTimeZone(TimeZones.Utc);SetStartDate(Entry.Time(Frames[0]).Date);SetEndDate(Entry.Time(Frames.Last()).Date);SetDateTime(Entry.Time(Frames[0]));SetCash(10000);SetBenchmark(t=>0m);SetBrokerageModel(new DenyOrders(this));
  StreamSymbol=AddData<ObservationBatch>("SIPOBS",Resolution.Tick,TimeZones.Utc,fillForward:false).Symbol;
  foreach(var b in Batches)b.Symbol=StreamSymbol;Initialized=true;
 }
 public override void OnData(Slice slice)
 {
  foreach(var pair in slice.Get<ObservationBatch>())
  {
   var b=pair.Value;if(b.Index!=Received||Entry.Ns(UtcTime)!=b.NativeNs)throw new InvalidOperationException("CALLBACK_ORDER_OR_CLOCK");
   var hash=Entry.Hash(Encoding.UTF8.GetBytes(b.Payload.ToString(Formatting.None)));if(hash!=b.PayloadHash)throw new InvalidOperationException("CALLBACK_PAYLOAD");
   trace.AppendData(Encoding.UTF8.GetBytes(b.NativeNs.ToString(System.Globalization.CultureInfo.InvariantCulture)+"|"+hash+"\n"));Received++;
   foreach(JObject e in b.Payload){if((bool)e["execution_admitted"]!)throw new InvalidOperationException("EXECUTION_FLAG");Events++;if((string)e["kind"]! =="bars")BarEvents++;else QuoteEvents++;}
  }
 }
 public override void OnEndOfAlgorithm(){Ended=true;Trace=Convert.ToHexStringLower(trace.GetHashAndReset());}
 public JObject Result()=>new JObject{["initialized"]=Initialized,["ended"]=Ended,["on_data_batches"]=Received,["events"]=Events,["bars"]=BarEvents,["quotes"]=QuoteEvents,["trace_sha256"]=Trace,["orders"]=0,["engine"]="AlgorithmManager.Run/SubscriptionSynchronizer/QCAlgorithm.OnData",["execution_admitted"]=false};
}
public sealed class DenyOrders:DefaultBrokerageModel
{
 readonly Diagnostic a;public DenyOrders(Diagnostic x){a=x;}
 public override bool CanSubmitOrder(Security s,Order o,out BrokerageMessageEvent message){a.DeniedSubmissions++;message=new BrokerageMessageEvent(BrokerageMessageType.Error,"DENY_ALL","No-order diagnostic");return false;}
}
public sealed class ObservationFeed:IDataFeed
{
 readonly Diagnostic a;public ObservationFeed(Diagnostic x){a=x;}public bool IsActive=>true;
 public void Initialize(IAlgorithm x,AlgorithmNodePacket j,IResultHandler r,IMapFileProvider m,IFactorFileProvider f,IDataProvider p,IDataFeedSubscriptionManager s,IDataFeedTimeProvider t,IDataChannelProvider c){}
 public Subscription CreateSubscription(SubscriptionRequest request)
 {
  var points=new List<SubscriptionData>();
  if(request.IsUniverseSubscription){var start=a.UtcTime;points.Add(new SubscriptionData(new BaseDataCollection(start.ConvertFromUtc(request.Configuration.ExchangeTimeZone),request.Configuration.Symbol,Array.Empty<BaseData>()),start));}
  else if(request.Configuration.Symbol==a.StreamSymbol)foreach(var b in a.Batches)points.Add(new SubscriptionData(b,Entry.Time(b.NativeNs)));
  return new Subscription(request,points.GetEnumerator(),new TimeZoneOffsetProvider(request.Configuration.ExchangeTimeZone,request.StartTimeUtc,request.EndTimeUtc));
 }
 public void RemoveSubscription(Subscription s){}public void Exit(){}
}
public sealed class ReplayClock:ITimeProvider{public DateTime Time;public DateTime GetUtcNow()=>Time;}
public sealed class ObservationStream:ISynchronizer
{
 readonly Diagnostic a;readonly DataManager manager;readonly UniverseSelection selection;
 public ObservationStream(Diagnostic x,DataManager m,UniverseSelection s){a=x;manager=m;selection=s;}
 public IEnumerable<TimeSlice> StreamData(CancellationToken token)
 {
  var clock=new ReplayClock{Time=Entry.Time(a.Frames[0])};var sync=new SubscriptionSynchronizer(selection,new PerformanceTrackingTool());sync.SetTimeProvider(clock);sync.SetTimeSliceFactory(new TimeSliceFactory(a.TimeZone));sync.SubscriptionFinished+=(s,sub)=>manager.RemoveSubscription(sub.Configuration);
  using var stream=sync.Sync(manager.DataFeedSubscriptions,token).GetEnumerator();
  foreach(var ns in a.Frames){clock.Time=Entry.Time(ns);do{if(!stream.MoveNext())throw new InvalidOperationException("SYNCHRONIZER_EARLY_END");yield return stream.Current;}while(stream.Current.IsTimePulse);}
 }
}
}
