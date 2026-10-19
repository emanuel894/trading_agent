using Newtonsoft.Json.Linq;
using QuantConnect;
using QuantConnect.Data.Market;
using QuantConnect.Orders;

public sealed partial class StageAlgorithm
{
    bool ProbeValuationEntry()
    {
        bool invoked=false;
        bool Guard(System.Func<bool> submit)=>!unknownClaim && submit();
        var accepted=Guard(()=>{invoked=true;return true;});
        if(accepted!=invoked)throw new System.InvalidOperationException("Valuation guard bypass");return accepted;
    }
    bool ProbeSpend(decimal amount)
    {
        bool invoked=false;
        bool Guard(System.Func<bool> submit)=>Portfolio.CashBook["USD"].Amount-encumbrance>=amount && submit();
        var accepted=Guard(()=>{invoked=true;return true;});
        if(accepted!=invoked)throw new System.InvalidOperationException("Cash guard bypass");return accepted;
    }
    JObject ClaimState()=>new JObject{["claim"]=Program.Num(claim),["claim_value"]=unknownClaim?null:Program.Num(settlement),["encumbered"]=!ProbeValuationEntry(),["valuation_entry_allowed"]=ProbeValuationEntry(),["action_applications"]=actionApplications,["native_profit"]=Program.Num(Securities[Symbols["I1"]].Holdings.Profit)};
    void Reverse(JObject e)
    {
        var kind=(string)e["kind"]!;
        if(kind=="reverse")
        {
            if(!Once("reverse",e))return;
            var security=Securities[Symbols["I1"]];var factor=Dec(e["factor"]!);
            var entitlement=security.Holdings.Quantity/factor;claim=entitlement-decimal.Floor(entitlement);
            if(claim!=Dec(e["claim"]!) || decimal.Floor(entitlement)!=Dec(e["whole"]!))throw new System.InvalidOperationException("Unproved fractional entitlement");
            // Prevent native cached-price fractional cash at ingress, rather than undoing it.
            security.Holdings.SetHoldings(security.Holdings.AveragePrice*factor,decimal.Floor(entitlement));
            SetQuote("I1",Dec(e["post_price"]!),Dec(e["post_price"]!)+0.02m);Portfolio.InvalidateTotalPortfolioValue();unknownClaim=true;actionApplications++;
            Snapshot("reverse",ClaimState());
        }
        else if(kind=="split_warning")Snapshot("duplicate_warning",ClaimState());
        else if(kind=="settle_claim")
        {
            if(Once("settle_claim",e))
            {
                if(e["evidence"]?.Type!=JTokenType.String || !unknownClaim)throw new System.InvalidOperationException("Missing claim settlement evidence");
                settlement=Dec(e["amount"]!);Portfolio.CashBook["USD"].AddAmount(settlement);claim=0;unknownClaim=false;paymentApplications++;
            }
            else{var extra=ClaimState();extra["settlement_applications"]=paymentApplications;Snapshot("settled",extra);}
        }
    }
    JObject DividendState(JObject ex)
    {
        var cash=Portfolio.CashBook["USD"].Amount;var security=Securities[Symbols["I1"]];
        // Native cash already contains the20 dividend: do not add receivable again to NAV.
        return new JObject{["receivable"]=Program.Num(receivable),["encumbrance"]=Program.Num(encumbrance),["spendable"]=Program.Num(cash-encumbrance),["economic_nav"]=Program.Num(cash+security.Holdings.Quantity*security.BidPrice),["request9001"]=ProbeSpend(9001m),["raw_bid"]=Program.Num(security.BidPrice),["dividend_applications"]=actionApplications,["payment_applications"]=paymentApplications,["payable_ns"]=ex["payable_ns"]!.DeepClone()};
    }
    void DividendCase(JObject e)
    {
        var ex=((JArray)Case["events"]!).Cast<JObject>().First(x=>(string)x["kind"]! == "dividend");
        if((string)e["kind"]! == "dividend")
        {
            if(Once("dividend",e))
            {
                Portfolio.ApplyDividend(new Dividend(Symbols["I1"],Program.Time(Now).ConvertFromUtc(TimeZones.NewYork),Dec(e["distribution"]!),100m),false,DataNormalizationMode.Raw);
                receivable=Securities[Symbols["I1"]].Holdings.Quantity*Dec(e["distribution"]!);encumbrance=receivable;actionApplications++;
                SetQuote("I1",Dec(e["post_price"]!),Dec(e["post_price"]!)+0.02m);
            }
            else Snapshot("ex_duplicate",DividendState(ex));
        }
        else if((string)e["kind"]! == "dividend_pay")
        {
            if(ex["payable_ns"]!.Type==JTokenType.Null || Program.Ns(ex["payable_ns"]!)>Now || e["evidence"]?.Type!=JTokenType.String)throw new System.InvalidOperationException("Unproved payment");
            if(Once("dividend_pay",e)){encumbrance=0;receivable=0;paymentApplications++;}
            else{SetQuote("I1",98m,98.02m);Snapshot("paid_duplicate",DividendState(ex));}
        }
    }
    decimal mergerOriginalCost,mergerCashConsideration;
    JObject MergerState()=>new JObject{["lineage"]="I1->I2",["original_cost"]=Program.Num(mergerOriginalCost),["native_carry_book_cost"]=Program.Num(Securities[Symbols["I2"]].Holdings.Quantity*Securities[Symbols["I2"]].Holdings.AveragePrice),["I2_raw_bid"]=Program.Num(Securities[Symbols["I2"]].BidPrice),["tax_basis_allocation"]=null,["economic_value"]=Program.Num(Securities[Symbols["I2"]].Holdings.Quantity*Securities[Symbols["I2"]].BidPrice+mergerCashConsideration),["valuation_entry_allowed"]=ProbeValuationEntry(),["unresolved"]=unknownClaim,["receivable"]=Program.Num(receivable),["payment_applications"]=paymentApplications};
    void Merger(JObject e)
    {
        if((string)e["kind"]! == "merger")
        {
            if(!Once("merger",e))return;
            if(e["evidence"]?.Type!=JTokenType.String || (bool)e["conflict"]!)
            {
                unknownClaim=true;
                Snapshot("unresolved",new JObject{["receivable"]=null,["lineage"]=null,["tax_basis_allocation"]=null,["economic_value"]=null,["valuation_entry_allowed"]=ProbeValuationEntry(),["unresolved"]=true});return;
            }
            var predecessor=Securities[Symbols["I1"]];var successor=Securities[Symbols[(string)e["successor"]!]];
            var quantity=predecessor.Holdings.Quantity;var original=quantity*predecessor.Holdings.AveragePrice;var next=quantity*Dec(e["ratio"]!);
            // Carry known aggregate book cost; external tax allocation remains null.
            predecessor.Holdings.SetHoldings(0m,0m);successor.Holdings.SetHoldings(original/next,next);receivable=quantity*Dec(e["cash_per_share"]!);mergerOriginalCost=original;mergerCashConsideration=receivable;
            SetQuote("I2",Dec(e["post_price"]!),Dec(e["post_price"]!)+0.02m);Portfolio.InvalidateTotalPortfolioValue();
            Snapshot("converted",MergerState());
        }
        else if((string)e["kind"]! == "merger_pay")
        {
            if(Once("merger_pay",e)){if(e["evidence"]?.Type!=JTokenType.String || Dec(e["amount"]!)!=receivable)throw new System.InvalidOperationException("Merger payment mismatch");Portfolio.CashBook["USD"].AddAmount(receivable);receivable=0;paymentApplications++;}
            else Snapshot("paid_duplicate",MergerState());
        }
    }
    readonly JArray mappingQuoteResults=new();
    void Rename(JObject e)
    {
        if((string)e["kind"]! == "rename")
        {
            if(!Once("rename",e))return;
            if(Variant!="exact")
            {unknownClaim=true;Snapshot("unresolved",new JObject{["mapping_version"]=1,["ticker"]="AAA",["unresolved"]=true,["entry_allowed"]=ProbeValuationEntry()});return;}
            var before=Symbols["I1"].ID;var order=tickets[0].OrderId;
            mapped=Symbols["I1"].UpdateMappedSymbol((string)e["ticker"]!);ticker=(string)e["ticker"]!;mappingVersion++;
            if(mapped.ID!=before)throw new System.InvalidOperationException("Mapped SID changed");
            Snapshot("mapped",new JObject{["mapping_version"]=mappingVersion,["ticker"]=ticker,["stable_sid"]=mapped.ID==before,["stable_order"]=tickets[0].OrderId==order,["stable_intent"]=tickets[0].Tag=="frozen fixture intent",["unresolved"]=false});
        }
        else if((string)e["kind"]! == "quote" && Variant=="exact")
        {
            var result=(string)e["ticker"]! == ticker?"ADMITTED":"SYMBOL_INTERVAL";mappingQuoteResults.Add((string)e["id"]!+":"+result);
            if(result=="ADMITTED")AdmitQuote(e);
            if((string)e["id"]! == "new_quote")Snapshot("quotes",new JObject{["quote_results"]=mappingQuoteResults,["mapping_version"]=mappingVersion,["ticker"]=ticker,["unresolved"]=false});
        }
    }
}
