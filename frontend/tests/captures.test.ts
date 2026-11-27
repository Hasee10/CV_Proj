import { describe, expect, it, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { createApiClient } from '../src/api/client';
import { isFieldResult, isVerifyResult, isBenchmarkResult } from '../src/api/results';
import type { CaptureManifest } from '../src/api/results';

const asset=(path:string)=>new URL('../public'+path,import.meta.url);
const latest=JSON.parse(readFileSync(asset('/results/latest.json'),'utf8')) as {manifest:string};
const manifest=JSON.parse(readFileSync(asset(latest.manifest),'utf8')) as CaptureManifest;
const response=(id:string)=>JSON.parse(readFileSync(asset(manifest.records.find(r=>r.id===id)!.response),'utf8'));
describe('Actual backend capture integrity',()=>{
  it('retains every exact response and source image hash',()=>{
    expect(manifest.records).toHaveLength(9);
    for(const record of manifest.records){
      expect(createHash('sha256').update(readFileSync(asset(record.response))).digest('hex')).toBe(record.response_sha256);
      expect(record.http_status).toBe(200);
      if(record.image){
        const bytes=readFileSync(asset(record.image));
        expect(createHash('sha256').update(bytes).digest('hex')).toBe(record.image_sha256);
        expect(bytes.equals(readFileSync(new URL('../../'+record.source_path,import.meta.url)))).toBe(true);
      }
    }
  });
  it.each([['sheet_accept','accept'],['sheet_flag','flag'],['sheet_review','review']])('preserves %s decision, request ID and ROI evidence',(id,decision)=>{
    const value=response(id);expect(isVerifyResult(value)).toBe(true);expect(value.decision).toBe(decision);
    expect(value.request_id).toBe(manifest.records.find(r=>r.id===id)!.request_id);
    expect(value.rois.numeric_px).toHaveLength(4);expect(value.rois.written_px).toHaveLength(4);
  });
  it('retains the benchmark exactly without recomputing metrics',()=>{
    const value=response('benchmark');expect(isBenchmarkResult(value)).toBe(true);
    const frozen=JSON.parse(readFileSync(new URL('../../artifacts/M8/COMPARATIVE_METRICS.json',import.meta.url),'utf8'));
    expect(value).toEqual({source:'artifacts/M8/COMPARATIVE_METRICS.json',...frozen});
  });
  it('preserves decimal strings, raw text and nulls; rejects invented numeric values',()=>{
    const value=response('numeric-proposed');expect(isFieldResult(value)).toBe(true);
    expect(typeof value.parsed_value).toBe('string');expect(isFieldResult({...value,parsed_value:3083})).toBe(false);
    expect(response('sheet_review').written.parsed_value).toBeNull();
  });
  it('uses the same exact input for the two numeric modes',()=>{
    const baseline=manifest.records.find(r=>r.id==='numeric-baseline')!,proposed=manifest.records.find(r=>r.id==='numeric-proposed')!;
    expect(baseline.image_sha256).toBe(proposed.image_sha256);
    expect(response('numeric-baseline').mode).toBe('baseline');expect(response('numeric-proposed').mode).toBe('proposed');
  });
  it('posts FormData without overriding the browser multipart boundary',async()=>{
    const fetcher=vi.fn<typeof fetch>().mockResolvedValue(new Response(JSON.stringify(response('sheet_accept'))));
    const body=new FormData();body.append('mode','baseline');
    const result=await createApiClient('http://localhost:8000',fetcher).verify(body);
    expect(result.decision).toBe('accept');expect(fetcher).toHaveBeenCalledWith('http://localhost:8000/api/verify',expect.objectContaining({method:'POST',body,headers:{Accept:'application/json'}}));
  });
  it('preserves structured POST busy failures for manual retry',async()=>{
    const fetcher=vi.fn<typeof fetch>().mockResolvedValue(new Response(JSON.stringify({error:{code:'busy',message:'Server occupied',request_id:'busy-request'}}),{status:503}));
    await expect(createApiClient('http://localhost:8000',fetcher).recognize(new FormData())).rejects.toMatchObject({code:'busy',status:503,requestId:'busy-request'});
  });
});
