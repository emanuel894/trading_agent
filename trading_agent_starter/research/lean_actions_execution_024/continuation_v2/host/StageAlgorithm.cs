using System.Globalization;
using Newtonsoft.Json.Linq;
using QuantConnect;
using QuantConnect.Algorithm;
using QuantConnect.Brokerages.Backtesting;
using QuantConnect.Data;
using QuantConnect.Data.Market;
using QuantConnect.Orders;
using QuantConnect.Orders.Fees;
using QuantConnect.Orders.Fills;
using QuantConnect.Securities;
using QuantConnect.Lean.Engine.TransactionHandlers;

// Fixture-specific projection, not a product engine or OMS.
public sealed partial class StageAlgorithm:QCAlgorithm
{
    public readonly JObject Input,Case;
    public readonly Dictionary<string,Symbol> Symbols=new(StringComparer.Ordinal);
    public readonly JArray Crosswalk=new(),Journal=new(),Snapshots=new(),Fills=new();
    public readonly List<long> Frames;
    public BacktestingTransactionHandler Transaction;
    public BacktestingBrokerage Brokerage;
    public bool EndObserved,Conflict;
    public bool Scripted=>Group=="Q19" || (Group=="Q20" && Variant=="partial");
    public string Group=>(string)Case["fixture"]!;
    public string Variant=>(string)Case["variant"]!;
    public long Decision=>Program.Ns(Case["decision_ns"]!);
    public long Now;
    public JObject Current;
    readonly List<JObject> pending;
    readonly List<OrderTicket> tickets=new();
    readonly Dictionary<string,string> evidence=new(StringComparer.Ordinal);
    readonly Dictionary<string,decimal> capacity=new(StringComparer.Ordinal);
    bool seeded,started,unknownClaim,cancelPending;
    decimal receivable,encumbrance,claim,settlement,charged;
    int actionApplications,paymentApplications,mappingVersion=1;
    string marketStatus="TRADABLE",ticker="AAA",lifecycle="SUBMITTED";
    Symbol mapped;
    public StageAlgorithm(JObject input,JObject test)
    {
        Input=input;Case=test;
        int i=0;
        foreach(var pair in new[]{("I1","AAA"),("I2","BBB"),("I3","AAB")})
        {
            var symbol=new Symbol(SecurityIdentifier.GenerateEquity(new DateTime(2025,1,1).AddDays(i++),pair.Item2,Market.USA),pair.Item2);
            Symbols.Add(pair.Item1,symbol);Crosswalk.Add(new JObject{["instrument"]=pair.Item1,["engine_sid"]=symbol.ID.ToString()});
        }
        mapped=Symbols["I1"];
        pending=((JArray)test["events"]!).Cast<JObject>().OrderBy(Available).ThenBy(x=>(int)x["sequence"]!).ThenBy(x=>(string)x["id"]!,StringComparer.Ordinal).ToList();
        Frames=new[]{Decision-2_000_000_000,Decision-1_000_000_000,Decision}.Concat(pending.Select(x=>Program.Ceiling(Available(x)))).Distinct().OrderBy(x=>x).ToList();Frames.Add(Frames.Max()+100);
        marketStatus=(string)test["initial_status"]??"TRADABLE";
    }
    static long Available(JObject e)=>Math.Max(Program.Ns(e["available_ns"]!),e["receipt_ns"]?.Type==JTokenType.Integer?Program.Ns(e["receipt_ns"]!):long.MinValue);
    static decimal Dec(JToken x)=>decimal.Parse((string)x!,CultureInfo.InvariantCulture);
    public override void Initialize()
    {
        SetStartDate(Program.Time(Decision).Date);SetEndDate(Program.Time(Frames.Max()).Date);SetTimeZone(TimeZones.NewYork);SetCash(Dec(Case["cash"]!));SetBenchmark(t=>0m);SetDateTime(Program.Time(Frames[0]));
        foreach(var s in Symbols.Values)
        {
            var security=AddSecurity(s,Resolution.Minute,fillForward:false,dataNormalizationMode:DataNormalizationMode.Raw);
            security.SetFillModel(new StageFill(this));security.SetSlippageModel(new QuantConnect.Orders.Slippage.ConstantSlippageModel(0));
            security.SetFeeModel(new ConstantFeeModel(Group=="Q20" && Variant=="total"?Math.Max(1m,Dec(Case["verified_total"]!)):1m));
        }
    }
    public override void OnData(Slice slice)
    {
        if(seeded)return;
        foreach(var s in Symbols.Values)Securities[s].SetMarketPrice(new TradeBar(Program.Time(Decision-1_000_000_000).ConvertFromUtc(TimeZones.NewYork),s,100m,100m,100m,100m,0m,TimeSpan.Zero));
        var seed=Dec(Case["seed"]!);if(seed>0)Securities[Symbols["I1"]].Holdings.SetHoldings(100m,seed);seeded=true;
    }
    public override void OnEndOfAlgorithm(){EndObserved=true;}
    public void Step(long dispatch)
    {
        if(!seeded && dispatch<Decision)return;
        if(!seeded)throw new InvalidOperationException("No native initialization");
        if(!started && dispatch>=Decision){started=true;Now=Decision;StartScenario();}
        while(pending.Count>0 && Program.Ceiling(Available(pending[0]))<=dispatch)
        {
            var e=pending[0];pending.RemoveAt(0);Now=Available(e);
            Journal.Add(new JObject{["record"]=e.DeepClone(),["admitted_ns"]=Now,["dispatch_ns"]=dispatch});
            Process(e);Current=null;
        }
    }
    OrderTicket Submit(decimal quantity,decimal? limit=null)
    {
        var t=limit.HasValue?LimitOrder(Symbols["I1"],quantity,limit.Value,tag:"frozen fixture intent"):
            MarketOrder(Symbols["I1"],quantity,asynchronous:true,tag:"frozen fixture intent");
        tickets.Add(t);Transaction.ProcessSynchronousEvents();
        if(t.GetMostRecentOrderResponse().IsError)throw new InvalidOperationException("Native order rejected: "+t.GetMostRecentOrderResponse());return t;
    }
    void StartScenario()
    {
        if(Group=="Q15")
        {
            var map=(JObject)Case["initial_mapping"]!;
            if(Program.Ns(map["available_ns"]!)>Now)throw new InvalidOperationException("Mapping unavailable");
            if(Variant=="exact")Submit(5,100);return;
        }
        if(Group=="Q16")
        {
            if(QuoteReason((JObject)Case["decision_quote"]!)==null && Variant!="exit")Submit(5);
            return;
        }
        if(Group=="Q17")Submit((string)Case["side"]! == "buy"?5:-5);
        if(Group=="Q19" || (Group=="Q20" && Variant=="partial"))Submit(10);
        if(Group=="Q20" && !Scripted)
        {
            var bound=Variant=="total"?new JValue(System.Math.Max(1m,Dec(Case["verified_total"]!))):Case["fee_evidence"] is JObject f?f["bound"]:Case["fee_bound"];
            feeBoundKnown=bound!=null && bound.Type!=JTokenType.Null && Dec(bound)>0m;
            if(feeBoundKnown)Submit(1);
        }
    }
    bool Once(string key,JObject record)
    {
        // Economic versions are stable; delivery duplicates do not create new actions.
        var economic=(JObject)record.DeepClone();economic.Remove("delivery_sequence");
        var bytes=economic.ToString(Newtonsoft.Json.Formatting.None);
        if(evidence.TryGetValue(key,out var prior)){if(prior!=bytes)throw new InvalidOperationException("Conflicting version "+key);return false;}
        evidence.Add(key,bytes);return true;
    }
    JObject Snapshot(string label,JObject extra)
    {
        var a=Securities[Symbols["I1"]].Holdings;var b=Securities[Symbols["I2"]].Holdings;
        var orders=new JArray(tickets.Select(t=>new JObject{["id"]=t.OrderId,["quantity"]=Program.Num(t.Quantity),["filled"]=Program.Num(t.QuantityFilled),["status"]=t.Status.ToString(),["limit"]=t.OrderType==OrderType.Limit?Program.Num(t.Get(OrderField.LimitPrice)):null}));
        var row=new JObject{["label"]=label,["at_ns"]=Now,["native_dispatch_ns"]=(UtcTime.Ticks-System.DateTime.UnixEpoch.Ticks)*100,["cash"]=Program.Num(Portfolio.CashBook["USD"].Amount),["I1_quantity"]=Program.Num(a.Quantity),["I1_average"]=Program.Num(a.AveragePrice),["I2_quantity"]=Program.Num(b.Quantity),["I2_average"]=Program.Num(b.AveragePrice),["fees"]=Program.Num(a.TotalFees+b.TotalFees),["orders"]=orders};
        foreach(var pair in extra)row[pair.Key]=pair.Value.DeepClone();Snapshots.Add(row);return row;
    }
    void SetQuote(string instrument,decimal bid,decimal ask)
    {
        var s=instrument=="I1"?mapped:Symbols[instrument];
        Securities[Symbols[instrument]].SetMarketPrice(new Tick{Symbol=s,Time=Program.Time(Now).ConvertFromUtc(TimeZones.NewYork),TickType=TickType.Quote,BidPrice=bid,AskPrice=ask,BidSize=1000,AskSize=1000});
    }
    public JObject Business()=>new JObject{["snapshots"]=Snapshots,["fills"]=Fills};
    public override void OnOrderEvent(OrderEvent e){}
    void Process(JObject e)
    {
        switch(Group)
        {
            case "Q12":Reverse(e);break;case "Q13":DividendCase(e);break;case "Q14":Merger(e);break;case "Q15":Rename(e);break;
            case "Q16":HaltCase(e);break;case "Q17":IsolatedFill(e);break;case "Q18":CapacityCase(e);break;case "Q19":ExecutionCase(e);break;case "Q20":FeeCase(e);break;
            default:throw new InvalidOperationException("Out of scope");
        }
    }
}
