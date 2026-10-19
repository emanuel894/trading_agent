using Newtonsoft.Json.Linq;
using QuantConnect;
using QuantConnect.Brokerages.Backtesting;
using QuantConnect.Data.Market;
using QuantConnect.Orders;
using QuantConnect.Orders.Fees;
using QuantConnect.Orders.Fills;
using QuantConnect.Securities;

public sealed partial class StageAlgorithm
{
    long resumedAt=long.MinValue;
    int rejectedCapacity;
    bool feeBoundKnown;
    decimal Reservation=>lifecycle=="CANCELED"?0m:(10m-Securities[Symbols["I1"]].Holdings.Quantity)*100.07001m+Math.Max(0m,1m-charged);
    public string QuoteReason(JObject q)
    {
        if((string)q["normalization"]! != "Raw")return "NORMALIZATION";
        if(Available(q)>Now)return "UNAVAILABLE";
        var age=Now-Program.Ns(q["event_ns"]!);if(age<0 || age>2_000_000_000)return "STALE";
        var bid=Dec(q["bid"]!);var ask=Dec(q["ask"]!);
        if(bid<=0 || ask<=bid || 10000m*(ask-bid)>20m*(ask+bid)/2m)return "PRICE";
        if((string)q["unit"]! != "shares" || Dec(q["size"]!)<=0 || (bool)q["gap"]! || q["conditions"] is not JArray c || c.Count!=1 || (string)c[0]! != "R")return "QUALITY";
        if(marketStatus!="TRADABLE")return "STATUS";
        if((string)q["session"]!="RTH" || !Securities[Symbols["I1"]].Exchange.Hours.IsOpen(Program.Time(Now).ConvertFromUtc(TimeZones.NewYork),false))return "SESSION";
        if(Group=="Q16" && resumedAt!=long.MinValue && Program.Ns(q["event_ns"]!)<=resumedAt)return "RESUME_FRESHNESS";
        return null;
    }
    void AdmitQuote(JObject e)
    {
        Current=null;if(QuoteReason(e)!=null)return;
        SetQuote("I1",Dec(e["bid"]!),Dec(e["ask"]!));
        var id=(string)e["id"]!;if(!capacity.ContainsKey(id))capacity.Add(id,Dec(e["size"]!)*0.1m);
        Current=e;Transaction.ProcessSynchronousEvents();
    }
    void HaltCase(JObject e)
    {
        var kind=(string)e["kind"]!;
        if(kind=="halt"){marketStatus="HALTED";Current=null;return;}
        if(kind=="resume")
        {
            marketStatus="TRADABLE";resumedAt=Now;Current=null;
            Snapshot("resumed",new JObject{["status"]=marketStatus,["executable_quote"]=null});return;
        }
        if(kind=="quote")
        {
            if(Variant=="exit" && tickets.Count==0)Submit(-5);
            AdmitQuote(e);
            if((string)e["id"]! == "q1_halted" && Variant!="unknown")Snapshot("halted",new JObject{["status"]=marketStatus,["executable_quote"]=null});
        }
        if(kind=="deadline")
        {
            if(Variant!="exit")foreach(var t in tickets.Where(t=>!t.Status.IsClosed())){t.Cancel("original D+5s deadline");Transaction.ProcessSynchronousEvents();}
            var extra=new JObject{["status"]=marketStatus,["deadline_ns"]=Decision+5_000_000_000};if(Variant=="unknown")extra["entry_allowed"]=false;Snapshot("finished",extra);
        }
    }
    void IsolatedFill(JObject e)
    {
        AdmitQuote(e);Snapshot("filled",new JObject{["stock_slippage"]="0"});
    }
    void CapacityCase(JObject e)
    {
        AdmitQuote(e);
        if((string)e["id"]! == "budget_q1")
        {
            Submit(3);Submit(3);
            if(rejectedCapacity!=2)throw new System.InvalidOperationException("Capacity rejection not observed");
            tickets[1].Cancel("frozen quantity exceeds remaining quote budget");Transaction.ProcessSynchronousEvents();
            Brokerage.Scan();Brokerage.Scan();Transaction.ProcessSynchronousEvents();
            Snapshot("same_event_scans",new JObject{["remaining_capacity"]=Program.Num(capacity[(string)e["id"]!]),["rejected_intent"]=rejectedCapacity});
        }
        else{Submit(3);Snapshot("new_event",new JObject{["remaining_capacity"]=Program.Num(capacity[(string)e["id"]!])});}
    }
    public OrderEvent Fill(Security security,Order order,decimal? limit)
    {
        var result=new OrderEvent(order,UtcTime,OrderFee.Zero);var q=Current;
        if(q==null || QuoteReason(q)!=null || order.Status.IsClosed())return result;
        if(Group=="Q16" && order.Direction==OrderDirection.Buy && (Now<Decision+1_000_000_000 || Now>Decision+5_000_000_000))return result;
        decimal bps=Group=="Q17"?(int)Case["bps"]!:5;
        var price=order.Direction==OrderDirection.Buy?security.AskPrice*(1m+bps/10000m):security.BidPrice*(1m-bps/10000m);
        if(limit.HasValue && ((order.Direction==OrderDirection.Buy && price>limit.Value)||(order.Direction==OrderDirection.Sell && price<limit.Value)))return result;
        var id=(string)q["id"]!;var quantity=System.Math.Abs(order.Quantity);
        if(capacity[id]<quantity){if(Group=="Q18")rejectedCapacity=order.Id;return result;}
        capacity[id]-=quantity;result.Status=OrderStatus.Filled;result.FillQuantity=order.Quantity;result.FillPrice=price;
        var fee=Group=="Q20" && Variant=="total"?System.Math.Max(1m,Dec(Case["verified_total"]!)):1m;
        // Native brokerage/fee/portfolio pipeline is the sole execution accounting owner.
        Fills.Add(new JObject{["order_id"]=order.Id,["quote_id"]=id,["quantity"]=Program.Num(order.Quantity),["price"]=Program.Num(price),["fee"]=Program.Num(fee),["available_ns"]=Now});return result;
    }
    void EmitExecution(JObject e)
    {
        if(!Once((string)e["id"]!,e))return;
        var target=System.Math.Max(1m,Dec(e["verified_fee"]!));var delta=target-charged;charged=target;
        var t=tickets[0];var order=Transactions.GetOrderById(t.OrderId);
        var fill=new OrderEvent(order,UtcTime,new OrderFee(new CashAmount(delta,"USD"))){Status=OrderStatus.PartiallyFilled,FillQuantity=Dec(e["qty"]!),FillPrice=Dec(e["price"]!)};
        ((ScriptedBrokerage)Brokerage).Emit(fill);Transaction.ProcessSynchronousEvents();
        Fills.Add(new JObject{["order_id"]=t.OrderId,["quote_id"]=e["id"]!.DeepClone(),["quantity"]=e["qty"]!.DeepClone(),["price"]=e["price"]!.DeepClone(),["fee"]=Program.Num(delta),["available_ns"]=Now});
    }
    void ExecutionCase(JObject e)
    {
        var kind=(string)e["kind"]!;
        if(kind=="execution")
        {
            var before=Fills.Count;EmitExecution(e);if(Fills.Count==before)return;
            if(!cancelPending)lifecycle="PARTIAL";
            Snapshot((string)e["id"]! == "e1"?"partial1":"partial2",new JObject{["reservation"]=Program.Num(Reservation),["lifecycle"]=lifecycle});
        }
        else if(kind=="cancel_request")
        {
            if(!Once("cancel_request",e))return;cancelPending=true;lifecycle="CANCEL_PENDING";tickets[0].Cancel("scripted cancel request");Transaction.ProcessSynchronousEvents();
            Snapshot("cancel_requested",new JObject{["reservation"]=Program.Num(Reservation),["lifecycle"]=lifecycle});
        }
        else if(kind=="cancel_ack")
        {
            if(!Once("cancel_ack",e))return;
            ((ScriptedBrokerage)Brokerage).Emit(new OrderEvent(Transactions.GetOrderById(tickets[0].OrderId),UtcTime,OrderFee.Zero){Status=OrderStatus.Canceled});Transaction.ProcessSynchronousEvents();lifecycle="CANCELED";
            Snapshot("canceled",new JObject{["reservation"]=Program.Num(Reservation),["lifecycle"]=lifecycle});
        }
        else if(kind=="stale_status")
        {
            if(lifecycle!="CANCELED" || tickets[0].Status!=OrderStatus.Canceled)throw new System.InvalidOperationException("Terminal status regressed");
        }
    }
    readonly JArray feeAdjustments=new();
    int corrections;
    void FeeCase(JObject e)
    {
        var kind=(string)e["kind"]!;
        if(Variant=="total")
        {
            AdmitQuote(e);Snapshot("filled",new JObject{["verified_total"]=Case["verified_total"]!.DeepClone()});return;
        }
        if(Variant=="partial")
        {
            if(kind=="execution")
            {EmitExecution(e);Snapshot("partial"+Fills.Count,new JObject{["cumulative_fee"]=Program.Num(charged)});}
            else if(kind=="cancel_request"){tickets[0].Cancel("scripted fee-case cancellation");Transaction.ProcessSynchronousEvents();}
            else if(kind=="cancel_ack")
            {((ScriptedBrokerage)Brokerage).Emit(new OrderEvent(Transactions.GetOrderById(tickets[0].OrderId),UtcTime,OrderFee.Zero){Status=OrderStatus.Canceled});Transaction.ProcessSynchronousEvents();Snapshot("canceled",new JObject{["cumulative_fee"]=Program.Num(charged)});}
            else if(kind=="fee_correction")
            {
                if(Once((string)e["id"]!,e))
                {
                    if(e["evidence"]?.Type!=JTokenType.String || tickets[0].Status!=OrderStatus.Canceled)throw new System.InvalidOperationException("Unproved fee correction");
                    var target=System.Math.Max(1m,Dec(e["verified_fee"]!));var delta=target-charged;charged=target;
                    var fee=new OrderFee(new CashAmount(delta,"USD"));fee.ApplyToPortfolio(Portfolio,new OrderEvent(Transactions.GetOrderById(tickets[0].OrderId),UtcTime,fee));Securities[Symbols["I1"]].Holdings.AddNewFee(delta);
                    feeAdjustments.Add(Program.Num(delta));corrections++;
                }
                else Snapshot("corrected_duplicate",new JObject{["cumulative_fee"]=Program.Num(charged),["fee_adjustments"]=feeAdjustments,["fee_correction_applications"]=corrections});
            }
            return;
        }
        if(Variant=="no_fill"){tickets[0].Cancel("unfilled fixture");Transaction.ProcessSynchronousEvents();}
        Snapshot("finished",new JObject{["fee_state"]=feeBoundKnown?"NO_FILL":"UNRESOLVED",["entry_allowed"]=feeBoundKnown});
    }
}
public sealed class StageFill:FillModel
{
    readonly StageAlgorithm algorithm;public StageFill(StageAlgorithm a){algorithm=a;}
    public override OrderEvent MarketFill(Security security,MarketOrder order)=>algorithm.Fill(security,order,null);
    public override OrderEvent LimitFill(Security security,LimitOrder order)=>algorithm.Fill(security,order,order.LimitPrice);
}
// Explicitly fake destination: no claim that ordinary backtesting emits partial fills.
public sealed class ScriptedBrokerage:BacktestingBrokerage
{
    public ScriptedBrokerage(StageAlgorithm a):base(a){}
    public override void Scan(){}
    public override bool CancelOrder(Order order)=>true; // ack arrives as separate evidence
    public void Emit(OrderEvent e)=>OnOrderEvent(e);
}
