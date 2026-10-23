using System.Globalization;
using Newtonsoft.Json.Linq;
using QuantConnect;
using QuantConnect.Algorithm;
using QuantConnect.Algorithm.Framework.Execution;
using QuantConnect.Algorithm.Framework.Portfolio;
using QuantConnect.Brokerages;
using QuantConnect.Brokerages.Backtesting;
using QuantConnect.Data;
using QuantConnect.Data.Market;
using QuantConnect.Lean.Engine.TransactionHandlers;
using QuantConnect.Orders;
using QuantConnect.Orders.Fees;
using QuantConnect.Orders.Fills;
using QuantConnect.Securities;

// Qualification-only adapter: engine holdings/cash remain the sole trade accounting owner.
public sealed partial class ResearchAlgorithm:QCAlgorithm
{
 public readonly JObject Case;
 public readonly Dictionary<string,Symbol> Symbols=new(StringComparer.Ordinal);
 public readonly List<long> Frames;
 public BacktestingTransactionHandler Transaction;public LocalBrokerage Brokerage;
 public bool EndObserved,Daily,Drawdown,NavKnown=true,PendingExit;
 public int GateCalls;public long Now,Decision,Due;
 public bool Scripted=>(bool?)Case["scripted"]==true;
 public JObject Current;
 readonly List<JObject> pending;readonly JArray decisions=new(),snapshots=new(),fills=new(),ranked=new(),riskRecords=new();
 readonly Dictionary<int,(string id,long ns)> fillSources=new();
 readonly Dictionary<int,Reservation> reservations=new();readonly Dictionary<string,OrderTicket> tickets=new(StringComparer.Ordinal);
 readonly HashSet<string> applied=new(StringComparer.Ordinal);readonly Dictionary<string,decimal> capacity=new();
 JObject context;bool seeded;decimal dayStart=10000m,highWater=10000m;DateTime lastSession;
 public ResearchAlgorithm(JObject c)
 {
  Case=c;Decision=(long?)c["start_ns"]??1736175600000000000;Due=(long?)c["exit_due_ns"]??0;Daily=(bool?)c["daily"]==true;lastSession=Program.Time(Decision).ConvertFromUtc(TimeZones.NewYork).Date;
  dayStart=c["day_start"]!=null?Program.Dec(c["day_start"]!):10000m;highWater=c["high_water"]!=null?Program.Dec(c["high_water"]!):10000m;if(c["initial_halt"] is JObject halt)riskRecords.Add(halt.DeepClone());
  for(int i=1;i<=7;i++)Symbols.Add("I"+i,new Symbol(SecurityIdentifier.GenerateEquity(new DateTime(2025,1,i),"SYN"+i,Market.USA),"SYN"+i));
  pending=((JArray)c["steps"]!).Cast<JObject>().OrderBy(s=>(long)s["at_ns"]!).ToList();
  Frames=new[]{Decision-2_000_000_000,Decision-1_000_000_000,Decision}.Concat(pending.Select(s=>Program.Ceiling((long)s["at_ns"]!))).Distinct().OrderBy(n=>n).ToList();Frames.Add(Frames.Max()+100);
 }
 public string Instrument(Symbol symbol)=>Symbols.Single(p=>p.Value==symbol).Key;
 string Issuer(string instrument)=>instrument=="I3"?"U1":"U"+instrument[1..];
 public string IntentFor(int id)=>reservations.TryGetValue(id,out var r)?(string)r.Intent["id"]!:Transactions.GetOrderById(id)?.Tag??"";
 bool Check(string name)=>((JArray)Case["checks"]!).Any(x=>(string)x! ==name);
 decimal Cash=>Portfolio.CashBook["USD"].Amount;
 decimal ReservedCash=>reservations.Values.Where(r=>r.Allowed&&!r.Closed&&r.Quantity>0).Sum(r=>r.Remaining*r.Price+r.FeeRemaining);
 decimal ReservedSell(string instrument)=>reservations.Values.Where(r=>!r.Closed&&r.Quantity<0&&r.Instrument==instrument).Sum(r=>r.Remaining);
 public override void Initialize()
 {
  SetStartDate(Program.Time(Decision).Date);SetEndDate(Program.Time(Frames.Max()).Date);SetTimeZone(TimeZones.NewYork);SetCash(Program.Dec(Case["cash"]!));SetBenchmark(t=>0m);SetDateTime(Program.Time(Frames[0]));
  Settings.MinimumOrderMarginPortfolioPercentage=0;Settings.FreePortfolioValuePercentage=0;
  SetBrokerageModel(new AdmissionModel(this));
  foreach(var symbol in Symbols.Values)
  {
   var security=AddSecurity(symbol,Resolution.Minute,fillForward:false,dataNormalizationMode:DataNormalizationMode.Raw);
   security.SetFeeModel(new ConstantFeeModel(1));security.SetSlippageModel(new QuantConnect.Orders.Slippage.ConstantSlippageModel(0));security.SetFillModel(new QuoteOnly(this));
  }
 }
 void Mark(string instrument,decimal price)=>Securities[Symbols[instrument]].SetMarketPrice(new TradeBar(Program.Time(Now).ConvertFromUtc(TimeZones.NewYork),Symbols[instrument],price,price,price,price,0m,TimeSpan.Zero));
 public override void OnData(Slice slice)
 {
  if(seeded)return;Now=Decision-1_000_000_000;
  foreach(var instrument in Symbols.Keys)Mark(instrument,Program.Dec(Case["mark"]!));
  foreach(var h in (JArray)Case["holdings"]!){var i=(string)h["instrument"]!;Mark(i,Program.Dec(h["mark"]!));Securities[Symbols[i]].Holdings.SetHoldings(Program.Dec(h["mark"]!),Program.Dec(h["qty"]!));}
  seeded=true;
 }
 public override void OnEndOfAlgorithm(){EndObserved=true;}
 public void Step(long dispatch)
 {
  if(!seeded&&dispatch<Decision)return;if(!seeded)throw new InvalidOperationException("Native initialization missing");
  while(pending.Count>0&&Program.Ceiling((long)pending[0]["at_ns"]!)<=dispatch)
  {
   var s=pending[0];pending.RemoveAt(0);Now=(long)s["at_ns"]!;var op=(string)s["op"]!;
   switch(op)
   {
    case "order":Submit(s);break;
    case "batch":foreach(var intent in ((JArray)s["intents"]!).Cast<JObject>().OrderBy(x=>(string)x["id"]!,StringComparer.Ordinal))Submit(intent);break;
    case "sized_order":Sized(s);break;
    case "rank":foreach(var c in ((JArray)s["candidates"]!).OrderByDescending(x=>Program.Dec(x["score"]!)).ThenBy(x=>(string)x["instrument"]!,StringComparer.Ordinal))ranked.Add(c["instrument"]!.DeepClone());break;
    case "snapshot":Snapshot((string)s["label"]!);break;
    case "quote":AdmitQuote(s);break;
    case "cancel_request":tickets[(string)s["id"]!].Cancel("frozen cancel request");Transaction.ProcessSynchronousEvents();break;
    case "cancel_ack":Acknowledge(s,OrderStatus.Canceled);break;
    case "reject":Acknowledge(s,OrderStatus.Invalid);break;
    case "execution":ApplyExecution(s);break;
    case "mark":RiskObservation(s);break;
    case "session":if((bool)s["explicit"]!){var session=(string)s["session_id"]!;var local=Program.Time(Now).ConvertFromUtc(TimeZones.NewYork);if(!NavKnown||session!=local.ToString("yyyy-MM-dd",CultureInfo.InvariantCulture)||local.Date<=lastSession||!Securities[Symbols["I1"]].Exchange.Hours.IsOpen(local,false))throw new InvalidOperationException("Invalid new-session evidence");riskRecords.Add(new JObject{["kind"]="session_reset",["at_ns"]=Now,["session_id"]=session,["day_start"]=Program.Num(Portfolio.TotalPortfolioValue),["high_water"]=Program.Num(highWater),["previous_daily"]=Daily});Daily=false;dayStart=Portfolio.TotalPortfolioValue;lastSession=local.Date;}break;
    case "schedule":ScheduleExit(s);break;
    case "due":if(!PendingExit){if(Due==0)Due=Now;PendingExit=true;Submit(new JObject{["id"]="EXIT",["qty"]=-Securities[Symbols["I1"]].Holdings.Quantity,["instrument"]="I1",["price"]="100.07001",["fee"]="1",["route"]="direct"});}break;
    default:throw new InvalidOperationException("Unknown fixture operation "+op);
   }
   Current=null;
  }
 }
 void Sized(JObject s)
 {
  if(s["sigma"]?.Type==JTokenType.Null||Program.Dec(s["sigma"]!)<=0){Record(s,false,"VOLATILITY",null,null,null);return;}
  var nav=Portfolio.TotalPortfolioValue;var cap=Math.Min(.1m*nav,.0025m*nav/Program.Dec(s["sigma"]!));
  var quantity=decimal.Floor((cap-Program.Dec(s["fee"]!))/Program.Dec(s["price"]!));
  var intent=(JObject)s.DeepClone();intent["qty"]=Program.Num(quantity);intent["route"]="direct";intent["budget"]=Program.Num(cap);Submit(intent);
 }
 void Submit(JObject intent)
 {
  if(context!=null)throw new InvalidOperationException("Reentrant intent admission");context=intent;
  try
  {
   var symbol=Symbols[(string)intent["instrument"]!];var quantity=Program.Dec(intent["qty"]!);var id=(string)intent["id"]!;
   var route=(string)intent["route"]??"direct";OrderTicket ticket=null;
   if(route=="setholdings")SetHoldings(symbol,.25m,liquidateExistingHoldings:false,tag:id);
   else if(route=="target")new ImmediateExecutionModel().Execute(this,new[]{new PortfolioTarget(symbol,Securities[symbol].Holdings.Quantity+quantity)});
   else ticket=MarketOrder(symbol,quantity,asynchronous:true,tag:id);
   Transaction.ProcessSynchronousEvents();
   if(ticket==null){var order=Transactions.GetOrders(o=>o.Symbol==symbol).OrderByDescending(o=>o.Id).FirstOrDefault();if(order!=null)ticket=Transactions.GetOrderTicket(order.Id);}
   if(ticket==null||!reservations.ContainsKey(ticket.OrderId))throw new InvalidOperationException("Native order did not reach admission gate: "+id);
   tickets[id]=ticket;
  }
  finally{context=null;}
 }
 void Record(JObject intent,bool allowed,string reason,string quantity,bool? gross,bool? symbol)
 {
  decisions.Add(new JObject{["id"]=intent["id"]!.DeepClone(),["allowed"]=allowed,["reason"]=reason,["quantity"]=quantity,["gross_ok"]=gross.HasValue?new JValue(gross.Value):JValue.CreateNull(),["symbol_ok"]=symbol.HasValue?new JValue(symbol.Value):JValue.CreateNull()});
 }
 public bool Admit(Order order,out BrokerageMessageEvent message)
 {
  lock(reservations)
  {
   message=null;if(reservations.TryGetValue(order.Id,out var known))return known.Allowed;
   GateCalls++;var intent=context??throw new InvalidOperationException("Unregistered native submission");var instrument=Instrument(order.Symbol);
   var r=new Reservation(intent,instrument,order.Quantity);reservations.Add(order.Id,r);
   string reason="OK";bool? gross=null,symbol=null;
   if(order.Quantity<0)
   {
    if((string)Case["destination_state"] is string state&&state!="READY")reason="DESTINATION_STATE";
    else if(-order.Quantity>Securities[order.Symbol].Holdings.Quantity-ReservedSell(instrument))reason="SELL_SHARES";
    if(Check("limits")){gross=true;symbol=true;}
   }
   else
   {
    if(Check("halts")&&NavKnown)RefreshRisk("admission:"+(string)intent["id"]!);
    if(Check("halts")&&!NavKnown)reason="NAV_UNKNOWN";
    else if(Check("halts")&&Daily)reason="DAILY_HALT";
    else if(Check("halts")&&Drawdown)reason="DRAWDOWN_HALT";
    else if(intent["price"]?.Type==JTokenType.Null)reason="PRICE_BOUND";
    else if(intent["fee"]?.Type==JTokenType.Null)reason="FEE_BOUND";
    else
    {
     r.Price=Program.Dec(intent["price"]!);r.FeeRemaining=Program.Dec(intent["fee"]!);
     if(r.Price<=0)reason="PRICE_BOUND";else if(r.FeeRemaining<0)reason="FEE_BOUND";
     else if(Check("cash")&&order.Quantity*r.Price+r.FeeRemaining>Cash-ReservedCash)reason="CASH";
     else if(Check("limits"))
     {
      var nav=Portfolio.TotalPortfolioValue;var exposure=Symbols.ToDictionary(p=>p.Key,p=>Math.Abs(Securities[p.Value].Holdings.HoldingsValue));
      foreach(var pending in reservations.Values.Where(x=>x.Allowed&&!x.Closed&&x.Quantity>0))exposure[pending.Instrument]+=pending.Remaining*pending.Price;
      gross=exposure.Values.Sum()+order.Quantity*r.Price<=nav*.6m;symbol=exposure[instrument]+order.Quantity*r.Price<=nav*.1m;
      var issuers=Symbols.Keys.Where(i=>Securities[Symbols[i]].Holdings.Quantity!=0||reservations.Values.Any(x=>x.Allowed&&!x.Closed&&x.Quantity>0&&x.Instrument==i)).Select(Issuer).ToHashSet();
      if(!gross.Value)reason="GROSS";else if(!symbol.Value)reason="SYMBOL";else if(!issuers.Contains(Issuer(instrument))&&issuers.Count>=5)reason="POSITIONS";else if(issuers.Contains(Issuer(instrument)))reason="ISSUER";
     }
    }
   }
   r.Allowed=reason=="OK";r.Closed=!r.Allowed;r.Remaining=r.Allowed?Math.Abs(order.Quantity):0;
   Record(intent,r.Allowed,reason,r.Allowed?Program.Num(order.Quantity):null,gross,symbol);
   if(!r.Allowed)message=new BrokerageMessageEvent(BrokerageMessageType.Warning,reason,"Frozen research admission rejected");return r.Allowed;
  }
 }
 public override void OnOrderEvent(OrderEvent e)
 {
  if(!reservations.TryGetValue(e.OrderId,out var r))return;
  if(e.Status is OrderStatus.Filled or OrderStatus.PartiallyFilled)
  {
   r.Remaining-=Math.Abs(e.FillQuantity);r.FeeRemaining=Math.Max(0,r.FeeRemaining-e.OrderFee.Value.Amount);
   if(r.Remaining<0)throw new InvalidOperationException("Fill exceeds reserved quantity");
   if(e.Status==OrderStatus.Filled||r.Remaining==0){r.Closed=true;if((string)r.Intent["id"]! =="EXIT")PendingExit=false;}
   var source=fillSources[e.OrderId];fills.Add(new JObject{["id"]=r.Intent["id"]!.DeepClone(),["quantity"]=Program.Num(e.FillQuantity),["price"]=Program.Num(e.FillPrice),["fee"]=Program.Num(e.OrderFee.Value.Amount),["source_id"]=source.id,["source_ns"]=source.ns,["native_dispatch_ns"]=(e.UtcTime.Ticks-DateTime.UnixEpoch.Ticks)*100});
   if(Check("halts")&&NavKnown)RefreshRisk("fill:"+(string)r.Intent["id"]!);
  }
  else if(e.Status is OrderStatus.Canceled or OrderStatus.Invalid){r.Remaining=0;r.Closed=true;}
 }
 void Acknowledge(JObject s,OrderStatus status)
 {
  var id=(string)s["id"]!;if(!applied.Add("ack:"+id))return;var order=Transactions.GetOrderById(tickets[id].OrderId);Brokerage.Emit(new OrderEvent(order,UtcTime,OrderFee.Zero){Status=status});Transaction.ProcessSynchronousEvents();
 }
 void ApplyExecution(JObject s)
 {
  if(!applied.Add("execution:"+(string)s["execution_id"]!))return;var order=Transactions.GetOrderById(tickets[(string)s["id"]!].OrderId);
  fillSources[order.Id]=((string)s["execution_id"]!,Now);Brokerage.Emit(new OrderEvent(order,UtcTime,new OrderFee(new CashAmount(Program.Dec(s["fee"]!),"USD"))){Status=OrderStatus.PartiallyFilled,FillQuantity=Program.Dec(s["qty"]!),FillPrice=Program.Dec(s["price"]!)});Transaction.ProcessSynchronousEvents();
 }
 void RiskObservation(JObject s)
 {
  var reference=(string)s["mark_ref"]!;
  if(s["equity"]?.Type==JTokenType.Null){riskRecords.Add(new JObject{["kind"]="mark",["at_ns"]=Now,["ref"]=reference,["equity"]=null});NavKnown=false;return;}
  var quantity=Securities[Symbols["I1"]].Holdings.Quantity;Mark("I1",(Program.Dec(s["equity"]!)-Cash)/quantity);var equity=Portfolio.TotalPortfolioValue;if(equity!=Program.Dec(s["equity"]!))throw new InvalidOperationException("Native marked equity differs from evidence");highWater=Math.Max(highWater,equity);
  riskRecords.Add(new JObject{["kind"]="mark",["at_ns"]=Now,["ref"]=reference,["equity"]=Program.Num(equity)});
  RefreshRisk(reference);
 }
 void RefreshRisk(string reference)
 {
  var equity=Portfolio.TotalPortfolioValue;highWater=Math.Max(highWater,equity);
  foreach(var reason in new[]{"DAILY_LOSS","DRAWDOWN"})
  {
   var trigger=reason=="DAILY_LOSS"?!Daily&&equity<=dayStart*.98m:!Drawdown&&equity<=highWater*.92m;if(!trigger)continue;
   if(reason=="DAILY_LOSS")Daily=true;else Drawdown=true;
   riskRecords.Add(new JObject{["kind"]="latch",["reason"]=reason,["at_ns"]=Now,["ref"]=reference,["equity"]=Program.Num(equity),["day_start"]=Program.Num(dayStart),["high_water"]=Program.Num(highWater)});
  }
 }
 void ScheduleExit(JObject s)
 {
  var closes=((JArray)s["closes_ns"]!).Select(x=>(long)x).ToArray();if(!closes.SequenceEqual(closes.OrderBy(x=>x))||closes.Distinct().Count()!=closes.Length)throw new InvalidOperationException("Calendar order invalid");
  var sessions=closes.Where(c=>Program.Time(c).ConvertFromUtc(TimeZones.NewYork).Date>=Program.Time(Now).ConvertFromUtc(TimeZones.NewYork).Date).ToArray();var index=(int)s["horizon"]!-1;
  if(index<0||index>=sessions.Length)throw new InvalidOperationException("Calendar incomplete");
  foreach(var close in sessions)
  {
   var local=Program.Time(close).ConvertFromUtc(TimeZones.NewYork);var hours=Securities[Symbols["I1"]].Exchange.Hours;
   if(hours.GetNextMarketClose(local.Date,false)!=local)throw new InvalidOperationException("Frozen calendar disagrees with native exchange hours");
  }
  Due=sessions[index]-300_000_000_000;
 }
 void AdmitQuote(JObject s)
 {
  Current=s;if((string)s["status"]! !="TRADABLE")return;
  var symbol=Symbols["I1"];Securities[symbol].SetMarketPrice(new Tick{Symbol=symbol,Time=Program.Time(Now).ConvertFromUtc(TimeZones.NewYork),TickType=TickType.Quote,BidPrice=Program.Dec(s["bid"]!),AskPrice=Program.Dec(s["ask"]!),BidSize=Program.Dec(s["size"]!),AskSize=Program.Dec(s["size"]!)});
  if(Check("halts")&&NavKnown)RefreshRisk((string)s["quote_id"]!);
  capacity[Now.ToString(CultureInfo.InvariantCulture)]=Program.Dec(s["size"]!)*.1m;Transaction.ProcessSynchronousEvents();
 }
 public OrderEvent Fill(Security security,Order order)
 {
  var e=new OrderEvent(order,UtcTime,OrderFee.Zero);var q=Current;if(q==null||(string)q["status"]! !="TRADABLE"||Instrument(order.Symbol)!="I1"||!reservations.TryGetValue(order.Id,out var r)||!r.Allowed||r.Closed)return e;
  if(!security.Exchange.Hours.IsOpen(Program.Time(Now).ConvertFromUtc(TimeZones.NewYork),false))return e;
  var buy=order.Quantity>0;var eligible=(string)r.Intent["id"]! =="EXIT"?Due+1_000_000_000:Decision+1_000_000_000;
  if(Now<eligible||(buy&&Now>Decision+5_000_000_000))return e;
  var bid=Program.Dec(q["bid"]!);var ask=Program.Dec(q["ask"]!);if(bid<=0||ask<=bid||10000m*(ask-bid)>20m*(ask+bid)/2m)return e;
  var price=buy?ask*1.0005m:bid*.9995m;if(buy&&price>r.Price)return e;
  var key=Now.ToString(CultureInfo.InvariantCulture);if(r.Remaining>capacity[key])return e;capacity[key]-=r.Remaining;
  fillSources[order.Id]=((string)q["quote_id"]!,Now);e.Status=OrderStatus.Filled;e.FillQuantity=buy?r.Remaining:-r.Remaining;e.FillPrice=price;return e;
 }
 void Snapshot(string label)=>snapshots.Add(new JObject{["label"]=label,["cash"]=Program.Num(Cash),["reserved_cash"]=Program.Num(ReservedCash),["free_cash"]=Program.Num(Cash-ReservedCash),["quantity"]=Program.Num(Securities[Symbols["I1"]].Holdings.Quantity),["reserved_sell"]=Program.Num(ReservedSell("I1")),["daily"]=Daily,["drawdown"]=Drawdown,["pending_exit"]=PendingExit});
 public JObject Business()=>new JObject{["decisions"]=decisions,["snapshots"]=snapshots,["fills"]=fills,["ranked"]=ranked,["due_ns"]=(string)Case["fixture"]! =="Q24"&&Due!=0?new JValue(Due):JValue.CreateNull(),["risk_records"]=riskRecords};
 sealed class Reservation
 {
  public readonly JObject Intent;public readonly string Instrument;public readonly decimal Quantity;public decimal Remaining,Price,FeeRemaining;public bool Allowed,Closed;
  public Reservation(JObject i,string instrument,decimal quantity){Intent=(JObject)i.DeepClone();Instrument=instrument;Quantity=quantity;}
 }
}
public sealed class AdmissionModel:DefaultBrokerageModel
{
 readonly ResearchAlgorithm a;public AdmissionModel(ResearchAlgorithm x){a=x;}
 public override bool CanSubmitOrder(Security security,Order order,out BrokerageMessageEvent message)=>a.Admit(order,out message);
 public override bool CanUpdateOrder(Security security,Order order,UpdateOrderRequest request,out BrokerageMessageEvent message){message=new BrokerageMessageEvent(BrokerageMessageType.Warning,"FROZEN_INTENT","Quantity/price updates forbidden");return false;}
}
public sealed class QuoteOnly:FillModel
{
 readonly ResearchAlgorithm a;public QuoteOnly(ResearchAlgorithm x){a=x;}
 public override OrderEvent MarketFill(Security security,MarketOrder order)=>a.Fill(security,order);
}
public sealed class LocalBrokerage:BacktestingBrokerage
{
 readonly ResearchAlgorithm a;public LocalBrokerage(ResearchAlgorithm x):base(x){a=x;}
 public override bool CancelOrder(Order order)=>true;
 public override void Scan(){if(!a.Scripted)base.Scan();}
 public void Emit(OrderEvent e)=>OnOrderEvent(e);
}
