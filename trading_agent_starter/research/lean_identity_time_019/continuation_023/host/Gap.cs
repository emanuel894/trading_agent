using System.Globalization;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using QuantConnect;
using QuantConnect.Data;
using QuantConnect.Data.Auxiliary;
using QuantConnect.Data.Market;
using QuantConnect.Interfaces;
using QuantConnect.Lean.Engine.DataFeeds.Enumerators;
using QuantConnect.Orders;

// Only the three Issue23 gaps. The preserved host and pinned LEAN stay untouched.
public sealed partial class IdentityAlgorithm
{
    readonly JArray knowledge=new(),history=new(),factorControls=new(),decoyJournal=new(),rawNormalization=new(),splitDelivery=new(),actionJournal=new();
    readonly Dictionary<string,string> actionVersions=new(StringComparer.Ordinal);
    List<JObject> gapPending;
    JObject BusinessPrefix,InitialSplit;
    int applications;
    public bool Coupling=>(bool?)Case["split_coupling"]==true;
    static long Admission(JObject r)=>Math.Max(Program.Ns(r["available_ns"]!),r["receipt_ns"]?.Type==JTokenType.Integer?Program.Ns(r["receipt_ns"]!):long.MinValue);
    void InitializeGap()
    {
        gapPending=((JArray)Case["future_records"]!).Concat((JArray)Case["factors"]!).Concat(Case["split_records"] as JArray??new JArray()).Cast<JObject>()
            .OrderBy(Admission).ThenBy(r=>(int)r["sequence"]!).ThenBy(r=>(string)r["id"]!,StringComparer.Ordinal).ToList();
        history.Add(Case["decision_quote"]!.DeepClone());
        if(Group=="Q11" && Case["adjusted_decoy"] is JObject d)gapPending.Add(d);
        gapPending=gapPending.OrderBy(Admission).ThenBy(r=>(int)r["sequence"]!).ThenBy(r=>(string)r["id"]!,StringComparer.Ordinal).ToList();
        Frames.Add(Program.Ceiling(Decision-2_000_000_000));
        foreach(var r in gapPending)Frames.Add(Program.Ceiling(Admission(r)));
        Frames.Add(Frames.Max()+100);
        Frames.Sort();
        for(int i=Frames.Count-1;i>0;i--)if(Frames[i]==Frames[i-1])Frames.RemoveAt(i);
    }
    JObject KnowledgeView(long ns)
    {
        var eligible=knowledge.Cast<JObject>().Where(x=>Program.Ns(x["admitted_ns"]!)<=ns).Select(x=>(JObject)x["record"]!).ToList();
        var q=(JObject)Case["decision_quote"]!;
        var correction=eligible.LastOrDefault(x=>(string)x["kind"]! == "correction");
        var projected=new JObject();
        foreach(var kind in new[]{"symbol","action","prediction"})projected[kind]=eligible.LastOrDefault(x=>(string)x["kind"]! == kind)?["payload"]?.DeepClone();
        return new JObject{["projections"]=projected,["asof_ns"]=ns,["q0_ask"]=Admission(q)<=ns?(correction?["ask"]??q["ask"])!.DeepClone():null,
            ["symbol_version"]=eligible.LastOrDefault(x=>(string)x["kind"]! == "symbol")?["version_id"]?.DeepClone(),
            ["action_version"]=eligible.LastOrDefault(x=>(string)x["kind"]! == "action")?["version_id"]?.DeepClone(),
            ["prediction_version"]=eligible.LastOrDefault(x=>(string)x["kind"]! == "prediction")?["version_id"]?.DeepClone()};
    }
    void ProcessGap(long dispatch)
    {
        if((string)Case["normalization"]! != "Raw")return;
        while(gapPending.Count>0 && Program.Ceiling(Admission(gapPending[0]))<=dispatch)
        {
            var r=gapPending[0];gapPending.RemoveAt(0);var ns=Admission(r);
            if(r["publication_ns"]?.Type==JTokenType.Integer && Program.Ns(r["publication_ns"]!)>ns)throw new InvalidOperationException("Publication after claimed admission");
            if(r["factor"]!=null && r["kind"]==null){FactorControl(r,dispatch);continue;}
            var kind=(string)r["kind"]!;
            if(kind=="quote")
            {
                var before=Program.Num(Securities[Symbols["I1"]].Price);
                var reason=Validate(r,ns);
                if(reason==null)throw new InvalidOperationException("Adjusted decoy admitted");
                decoyJournal.Add(new JObject{["id"]=r["id"]!.DeepClone(),["admitted_ns"]=ns,["dispatch_ns"]=dispatch,["result"]=reason,["native_price_before"]=before,["native_price_after"]=Program.Num(Securities[Symbols["I1"]].Price)});
                continue;
            }
            if(kind.StartsWith("split_",StringComparison.Ordinal)){ApplyIntegral(r,dispatch);actionJournal.Add(new JObject{["record"]=r.DeepClone(),["admitted_ns"]=ns,["dispatch_ns"]=dispatch,["owner"]="public_action_projection",["result"]=splitDelivery.Last!.DeepClone(),["applications"]=applications});continue;}
            if(!new[]{"correction","symbol","action","prediction"}.Contains(kind))throw new InvalidOperationException("Unknown typed ingress");
            var beforeView=KnowledgeView(ns-1);
            if(kind=="correction")
            {
                if((string)r["revision_of"]! != "q0")throw new InvalidOperationException("Unknown revision target");
                history.Add(r.DeepClone());
            }
            var item=new JObject{["record"]=r.DeepClone(),["admitted_ns"]=ns,["dispatch_ns"]=dispatch,["before"]=beforeView};
            knowledge.Add(item);item["after"]=KnowledgeView(ns);
        }
    }
    SubscriptionDataConfig NormalizationConfig(Symbol symbol,DataNormalizationMode mode)=>new SubscriptionDataConfig(typeof(Tick),symbol,Resolution.Tick,TimeZones.NewYork,TimeZones.NewYork,false,false,false,dataNormalizationMode:mode);
    static Tick Quote(Symbol symbol,long ns,decimal bid,decimal ask)=>new Tick{Symbol=symbol,Time=Program.Time(ns).ConvertFromUtc(TimeZones.NewYork),TickType=TickType.Quote,BidPrice=bid,AskPrice=ask,BidSize=1000m,AskSize=1000m};
    Tick NormalizeRaw(JObject r,Symbol symbol)
    {
        var provider=new FrozenFactors(symbol,0.5m);
        var config=NormalizationConfig(symbol,DataNormalizationMode.Raw);
        using var e=new PriceScaleFactorEnumerator(new List<BaseData>{Quote(symbol,Program.Ns(r["event_ns"]!),decimal.Parse((string)r["bid"]!,CultureInfo.InvariantCulture),decimal.Parse((string)r["ask"]!,CultureInfo.InvariantCulture))}.GetEnumerator(),config,provider);
        if(!e.MoveNext())throw new InvalidOperationException("Raw normalization empty");
        var tick=(Tick)e.Current;
        if(provider.Calls!=0 || Program.Num(tick.BidPrice)!=(string)r["bid"]! || Program.Num(tick.AskPrice)!=(string)r["ask"]!)throw new InvalidOperationException("Raw normalization substituted price");
        rawNormalization.Add(new JObject{["id"]=r["id"]!.DeepClone(),["provider_calls"]=provider.Calls,["bid"]=Program.Num(tick.BidPrice),["ask"]=Program.Num(tick.AskPrice),["mode"]=config.DataNormalizationMode.ToString()});
        return tick;
    }
    void FactorControl(JObject r,long dispatch)
    {
        var symbol=Symbols["I1"];var factor=decimal.Parse((string)r["factor"]!,CultureInfo.InvariantCulture);
        var provider=new FrozenFactors(symbol,factor);var config=NormalizationConfig(symbol,DataNormalizationMode.Adjusted);
        var before=Program.Num(Securities[symbol].Price);
        // Fresh immutable control for each admitted version: native refresh is daily.
        var probe=(JObject)Case["factor_probe"]!;
        if(Admission(probe)>Admission(r))throw new InvalidOperationException("Factor probe not yet available");
        using var e=new PriceScaleFactorEnumerator(new List<BaseData>{Quote(symbol,Program.Ns(probe["event_ns"]!),decimal.Parse((string)probe["bid"]!,CultureInfo.InvariantCulture),decimal.Parse((string)probe["ask"]!,CultureInfo.InvariantCulture))}.GetEnumerator(),config,provider);
        if(!e.MoveNext())throw new InvalidOperationException("Factor control empty");
        var tick=(Tick)e.Current;
        var decoy=(JObject)probe.DeepClone();decoy["normalization"]="Adjusted";decoy["bid"]=Program.Num(tick.BidPrice);decoy["ask"]=Program.Num(tick.AskPrice);
        // Admission rejection is before SetMarketPrice; factor control never trades.
        var result=Validate(decoy,Admission(r));
        factorControls.Add(new JObject{["record"]=r.DeepClone(),["admitted_ns"]=Admission(r),["dispatch_ns"]=dispatch,["provider_calls"]=provider.Calls,
            ["mode"]=config.DataNormalizationMode.ToString(),["scale"]=Program.Num(config.PriceScaleFactor),["bid"]=Program.Num(tick.BidPrice),["ask"]=Program.Num(tick.AskPrice),
            ["normalized_probe"]=decoy,["admission_result"]=result,["native_price_before"]=before,["native_price_after"]=Program.Num(Securities[symbol].Price)});
    }
    JObject SplitSnapshot()
    {
        var security=Securities[Symbols["I1"]];
        return new JObject{["quantity"]=Program.Num(security.Holdings.Quantity),["average"]=Program.Num(security.Holdings.AveragePrice),
            ["pending_quantity"]=Program.Num(ticket.Quantity),["pending_limit"]=Program.Num(ticket.Get(OrderField.LimitPrice)),
            ["reserved_notional"]=Program.Num(ticket.Quantity*ticket.Get(OrderField.LimitPrice)),["fee_bound"]="1",["cash"]=Program.Num(Portfolio.CashBook["USD"].Amount),["profit"]=Program.Num(security.Holdings.Profit)};
    }
    void ApplyIntegral(JObject r,long dispatch)
    {
        if(!Coupling || (string)r["factor"]! != "0.5" || Program.Ns(r["effective_ns"]!)!=Decision+3600_000_000_000)throw new InvalidOperationException("Out-of-scope action");
        if(Admission(r)<Program.Ns(r["effective_ns"]!))throw new InvalidOperationException("Early split");
        if((string)r["kind"]! == "split_warning"){splitDelivery.Add("WARNING_NO_APPLY");return;}
        var id=(string)r["id"]!;var version=(string)r["version_id"]!;
        if(actionVersions.TryGetValue(id,out var prior))
        {
            if(prior!=version)throw new InvalidOperationException("Conflicting split version");
            splitDelivery.Add("DUPLICATE_NO_APPLY");return;
        }
        var security=Securities[Symbols["I1"]];
        var split=new Split(Symbols["I1"],Program.Time(Program.Ns(r["effective_ns"]!)).ConvertFromUtc(TimeZones.NewYork),100m,0.5m,SplitType.SplitOccurred);
        // Sole owner. No Split is delivered to automatic AlgorithmManager processing.
        Portfolio.ApplySplit(split,security,false,DataNormalizationMode.Raw);
        BrokerageModel.ApplySplit(Transactions.GetOpenOrderTickets(t=>t.Symbol==split.Symbol).ToList(),split);
        Transaction.ProcessSynchronousEvents();
        if(ticket.UpdateRequests.Any(x=>x.Response.IsError))throw new InvalidOperationException("Native split order update rejected");
        actionVersions.Add(id,version);applications++;splitDelivery.Add("APPLIED");
    }
    public JObject GapBusiness()
    {
        if(Coupling)
        {
            var snapshot=SplitSnapshot();snapshot["owner"]="public_action_projection";snapshot["applications"]=applications;
            snapshot["post_bid"]=Program.Num(Securities[Symbols["I1"]].BidPrice);snapshot["post_ask"]=Program.Num(Securities[Symbols["I1"]].AskPrice);
            snapshot["native_fill_count"]=orderStatuses.Count(x=>x=="Filled" || x=="PartiallyFilled");
            foreach(var key in new[]{"quantity","average","pending_quantity","pending_limit","reserved_notional"})snapshot["initial_"+key]=InitialSplit[key]!.DeepClone();
            return new JObject{["split"]=snapshot,["split_delivery"]=splitDelivery,["action_journal"]=actionJournal};
        }
        return new JObject{["business_prefix"]=BusinessPrefix,["knowledge"]=knowledge,["history"]=history,["factor_controls"]=factorControls,["decoy_journal"]=decoyJournal,["raw_normalization"]=rawNormalization,["metadata_rejected"]=(string)Case["normalization"]! != "Raw"};
    }
}
public sealed class FrozenFactors:IFactorFileProvider
{
    readonly Symbol symbol;readonly decimal factor;public int Calls;
    public FrozenFactors(Symbol s,decimal f){symbol=s;factor=f;}
    public void Initialize(IMapFileProvider m,IDataProvider d){}
    public IFactorProvider Get(Symbol s)
    {
        if(s!=symbol)throw new InvalidOperationException("Factor identity mismatch");Calls++;
        return new CorporateFactorProvider(s.Value,new[]{new CorporateFactorRow(new DateTime(2025,1,6),1m,factor,100m)});
    }
}
